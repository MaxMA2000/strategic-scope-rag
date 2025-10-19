import asyncio
import hashlib
import json
import time
from pathlib import Path
from typing import List, Optional, Set, Dict, Any
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser
import uuid

import httpx
from trafilatura import extract
from bs4 import BeautifulSoup

from core import settings, logger
from core.models import CrawlJobStatus, CrawlStatusResponse


class CrawlService:
    """Handle web crawling with robots.txt respect."""
    
    def __init__(self):
        self.data_root = Path(settings.data_root)
        self.jobs: Dict[str, Dict[str, Any]] = {}
    
    def _crawl_dir(self, project_id: str, job_id: str) -> Path:
        """Get crawl job directory."""
        p = self.data_root / project_id / "crawls" / job_id
        p.mkdir(parents=True, exist_ok=True)
        return p
    
    async def run_crawl(
        self,
        job_id: str,
        project_id: str,
        seed_urls: List[str],
        max_depth: int,
        max_pages: int,
        allow_render: bool,
        include_patterns: Optional[List[str]],
        exclude_patterns: Optional[List[str]]
    ):
        """Run crawl job."""
        try:
            logger.info(f"Starting crawl job {job_id} for project {project_id}")
            
            # Initialize job status
            self.jobs[job_id] = {
                "job_id": job_id,
                "status": CrawlJobStatus.RUNNING,
                "progress": 0.0,
                "pages_crawled": 0,
                "pages_total": None,
                "error_message": None
            }
            
            crawl_dir = self._crawl_dir(project_id, job_id)
            visited: Set[str] = set()
            to_visit: List[tuple] = [(url, 0) for url in seed_urls]  # (url, depth)
            pages_data = []
            
            async with httpx.AsyncClient(
                timeout=30.0,
                follow_redirects=True,
                headers={"User-Agent": settings.crawl_user_agent}
            ) as client:
                
                while to_visit and len(visited) < max_pages:
                    url, depth = to_visit.pop(0)
                    
                    if url in visited:
                        continue
                    if depth > max_depth:
                        continue
                    
                    # Check robots.txt
                    if not await self._check_robots(client, url):
                        logger.info(f"Skipping {url} (robots.txt)")
                        continue
                    
                    # Crawl page
                    try:
                        await asyncio.sleep(1.0 / settings.crawl_rate_limit)
                        response = await client.get(url)
                        response.raise_for_status()
                        
                        html = response.text
                        visited.add(url)
                        
                        # Extract content
                        content = extract(html, include_tables=True, include_comments=False)
                        if not content:
                            continue
                        
                        # Save page
                        page_data = {
                            "url": url,
                            "depth": depth,
                            "title": self._extract_title(html),
                            "content": content,
                            "crawled_at": time.time()
                        }
                        pages_data.append(page_data)
                        
                        # Save to disk
                        page_file = crawl_dir / f"page_{hashlib.md5(url.encode()).hexdigest()[:12]}.json"
                        page_file.write_text(json.dumps(page_data, indent=2))
                        
                        # Update status
                        self.jobs[job_id]["pages_crawled"] = len(visited)
                        self.jobs[job_id]["progress"] = min(len(visited) / max_pages, 1.0)
                        
                        logger.info(f"Crawled ({len(visited)}/{max_pages}): {url}")
                        
                        # Extract links for next depth
                        if depth < max_depth:
                            links = self._extract_links(html, url)
                            for link in links:
                                if link not in visited and self._should_crawl(link, include_patterns, exclude_patterns):
                                    to_visit.append((link, depth + 1))
                    
                    except Exception as e:
                        logger.warning(f"Failed to crawl {url}: {e}")
            
            # Save manifest
            manifest = {
                "job_id": job_id,
                "project_id": project_id,
                "seed_urls": seed_urls,
                "pages_crawled": len(visited),
                "completed_at": time.time()
            }
            (crawl_dir / "manifest.json").write_text(json.dumps(manifest, indent=2))
            
            # Update status
            self.jobs[job_id]["status"] = CrawlJobStatus.COMPLETED
            self.jobs[job_id]["progress"] = 1.0
            
            logger.info(f"Crawl job {job_id} completed: {len(visited)} pages")
        
        except Exception as e:
            logger.error(f"Crawl job {job_id} failed: {e}", exc_info=True)
            self.jobs[job_id]["status"] = CrawlJobStatus.FAILED
            self.jobs[job_id]["error_message"] = str(e)
    
    async def get_status(self, job_id: str) -> Optional[CrawlStatusResponse]:
        """Get crawl job status."""
        if job_id not in self.jobs:
            return None
        return CrawlStatusResponse(**self.jobs[job_id])
    
    async def _check_robots(self, client: httpx.AsyncClient, url: str) -> bool:
        """Check if URL is allowed by robots.txt."""
        try:
            parsed = urlparse(url)
            robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
            
            response = await client.get(robots_url, timeout=5.0)
            if response.status_code != 200:
                return True
            
            rp = RobotFileParser()
            rp.parse(response.text.splitlines())
            return rp.can_fetch(settings.crawl_user_agent, url)
        except:
            return True
    
    def _extract_title(self, html: str) -> Optional[str]:
        """Extract page title."""
        try:
            soup = BeautifulSoup(html, "lxml")
            title = soup.find("title")
            return title.get_text().strip() if title else None
        except:
            return None
    
    def _extract_links(self, html: str, base_url: str) -> List[str]:
        """Extract absolute links from HTML."""
        links = []
        try:
            soup = BeautifulSoup(html, "lxml")
            for a in soup.find_all("a", href=True):
                href = a["href"]
                absolute_url = urljoin(base_url, href)
                # Only same domain
                if urlparse(absolute_url).netloc == urlparse(base_url).netloc:
                    links.append(absolute_url)
        except:
            pass
        return links
    
    def _should_crawl(self, url: str, include_patterns: Optional[List[str]], exclude_patterns: Optional[List[str]]) -> bool:
        """Check if URL matches crawl filters."""
        # Simple pattern matching
        if exclude_patterns:
            for pattern in exclude_patterns:
                if pattern in url:
                    return False
        
        if include_patterns:
            for pattern in include_patterns:
                if pattern in url:
                    return True
            return False
        
        return True

