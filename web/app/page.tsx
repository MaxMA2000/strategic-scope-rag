'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';

export default function Home() {
  const router = useRouter();
  
  useEffect(() => {
    router.push('/chat');
  }, [router]);

  return (
    <div className="flex items-center justify-center h-screen bg-[#1a1b1e]">
      <div className="text-[#b5bac1]">Redirecting to chat...</div>
    </div>
  );
}
