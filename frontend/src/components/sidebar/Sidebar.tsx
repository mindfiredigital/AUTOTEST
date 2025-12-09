import React from "react";
import { cn } from "@/lib/utils";
import { useSidebar } from "@/contexts/SidebarContext";
import mindfireLogo from "@/assets/mindfire-logo.png";
import { menuItems } from "@/constants/menuItems";

export const Sidebar: React.FC = () => {
  const { isCollapsed } = useSidebar();

  return (
    <aside
      className={cn(
        "fixed left-0 top-0 h-screen border-r border-border bg-background z-20 hidden lg:flex flex-col transition-all duration-300",
        isCollapsed ? "w-20" : "w-[260px]"
      )}
    >
      <div className="flex items-center justify-center h-[72px] border-b border-border">
        {!isCollapsed ? (
          <img src={mindfireLogo} alt="Logo" className="h-[60px]" />
        )
          : <img src='https://ourgoalplan.co.in/Images/fire-logo.png' alt="Logo" className="h-[60px]" />}
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
              {!isCollapsed && <span className={cn(
                "text-base font-medium",
                item.active ? "text-foreground" : "text-muted-foreground"
              )}>
                {item.label}
              </span>}
            </button>
          );
        })}
      </nav>
    </aside>
  );
};
