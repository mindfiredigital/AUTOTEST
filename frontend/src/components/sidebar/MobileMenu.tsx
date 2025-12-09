import React from "react";
import { X } from "lucide-react";
import { cn } from "@/lib/utils";
import { useSidebar } from "@/contexts/SidebarContext";
import { menuItems } from "@/constants/menuItems";

export const MobileMenu: React.FC = () => {
  const { isOpen, close } = useSidebar();

  if (!isOpen) return null;

  return (
    <>
      <div
        className="fixed inset-0 bg-black/50 z-40 lg:hidden"
        onClick={close}
        aria-hidden="true"
      />

      <aside className="fixed left-0 top-0 h-screen w-[260px] border-r border-border bg-background z-50 lg:hidden transition-transform">
        <div className="flex h-full flex-col">

          <div className="h-[72px] border-b border-border flex items-center justify-end px-4">
            <button onClick={close} aria-label="Close menu">
              <X className="h-6 w-6" />
            </button>
          </div>

          <nav className="flex-1 pt-0">
            {menuItems.map((item) => {
              const Icon = item.icon;
              return (
                <button
                  key={item.id}
                  className={cn(
                    "relative flex w-full items-center gap-4 px-5 py-4 text-left transition-colors",
                    "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2",
                    item.active
                      ? "bg-accent"
                      : "hover:bg-accent/50"
                  )}
                  aria-label={item.label}
                  aria-current={item.active ? 'page' : undefined}
                  onClick={close}
                >
                  {item.active && (
                    <div className="absolute right-0 top-0 h-full w-1.5 bg-primary" />
                  )}
                  <div className={cn(
                    "flex h-6 w-6 items-center justify-center",
                    item.active ? "text-foreground" : "text-muted-foreground"
                  )}>
                    <Icon className="h-6 w-6 text-muted-foreground" />
                  </div>
                  <span className={cn(
                    "text-base font-medium",
                    item.active ? "text-foreground" : "text-muted-foreground"
                  )}>
                    {item.label}
                  </span>
                </button>
              );
            })}
          </nav>

          {/* Footer */}
          <div className="border-t border-border p-4">
            <div className="flex items-center justify-center">
              <div className="h-12 w-24 bg-muted rounded" />
            </div>
          </div>
        </div>
      </aside>
    </>
  );
};
