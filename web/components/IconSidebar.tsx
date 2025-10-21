'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { MessageSquare, FolderOpen, FileText, Activity, Settings, Moon, Bot } from 'lucide-react';
import { clsx } from 'clsx';

const navItems = [
  { href: '/chat', icon: MessageSquare, label: 'Chat', color: 'bg-teal-500' },
  { href: '/projects', icon: FolderOpen, label: 'Projects', color: 'bg-blue-500' },
  { href: '/documents', icon: FileText, label: 'Documents', color: 'bg-purple-500' },
  { href: '/jobs', icon: Activity, label: 'Jobs', color: 'bg-orange-500' },
];

export function IconSidebar() {
  const pathname = usePathname();

  return (
    <div className="w-16 bg-[#1a1b1e] flex flex-col items-center py-4 gap-3 border-r border-[#3f4147]">
      {/* Logo */}
      <Link
        href="/"
        className="w-10 h-10 rounded-lg bg-gradient-to-br from-teal-500 to-green-600 flex items-center justify-center mb-4 hover:opacity-80 transition-opacity"
      >
        <Bot className="text-white" size={24} />
      </Link>

      {/* Navigation Icons */}
      {navItems.map((item) => {
        const Icon = item.icon;
        const isActive = pathname.startsWith(item.href);
        
        return (
          <Link
            key={item.href}
            href={item.href}
            className={clsx(
              'w-10 h-10 rounded-lg flex items-center justify-center transition-all relative group',
              isActive
                ? `${item.color} text-white shadow-lg`
                : 'bg-[#2b2d31] text-[#b5bac1] hover:bg-[#383a40]'
            )}
            title={item.label}
          >
            <Icon size={20} />
            
            {/* Tooltip */}
            <div className="absolute left-full ml-2 px-3 py-1 bg-[#2b2d31] text-white text-sm rounded-md opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none whitespace-nowrap z-50 shadow-lg">
              {item.label}
            </div>
          </Link>
        );
      })}

      {/* Bottom Icons */}
      <div className="mt-auto flex flex-col gap-3">
        <button
          className="w-10 h-10 rounded-lg bg-[#2b2d31] text-[#b5bac1] hover:bg-[#383a40] flex items-center justify-center transition-all group"
          title="Settings"
        >
          <Settings size={20} />
          <div className="absolute left-full ml-2 px-3 py-1 bg-[#2b2d31] text-white text-sm rounded-md opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none whitespace-nowrap z-50 shadow-lg">
            Settings
          </div>
        </button>
        
        <button
          className="w-10 h-10 rounded-lg bg-[#2b2d31] text-[#b5bac1] hover:bg-[#383a40] flex items-center justify-center transition-all group"
          title="Dark Mode"
        >
          <Moon size={20} />
          <div className="absolute left-full ml-2 px-3 py-1 bg-[#2b2d31] text-white text-sm rounded-md opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none whitespace-nowrap z-50 shadow-lg">
            Dark Mode
          </div>
        </button>
      </div>
    </div>
  );
}

