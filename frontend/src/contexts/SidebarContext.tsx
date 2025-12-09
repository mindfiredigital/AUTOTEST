import React, { createContext, useContext, useState } from "react";

interface SidebarContextType {
    isOpen: boolean;
    toggle: () => void;
    close: () => void;
    isCollapsed: boolean;
    collapse: () => void;
}

const SidebarContext = createContext<SidebarContextType | undefined>(undefined);

export const SidebarProvider = ({ children }: { children: React.ReactNode }) => {
    const [isOpen, setIsOpen] = useState(false);
    const [isCollapsed, setIsCollapsed] = useState(false);

    const toggle = () => setIsOpen(prev => prev === false ? true : false);
    const close = () => setIsOpen(false);
    const collapse = () => setIsCollapsed(prev => !prev);

    return (
        <SidebarContext.Provider value={{ isOpen, toggle, isCollapsed, collapse, close }}>
            {children}
        </SidebarContext.Provider>
    );
};

export const useSidebar = () => {
    const context = useContext(SidebarContext);
    if (!context) throw new Error("useSidebar must be used inside SidebarProvider");
    return context;
};
