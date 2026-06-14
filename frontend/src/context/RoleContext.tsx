"use client";

import React, { createContext, useContext, useState, useEffect, ReactNode } from "react";

export type UserRole = "ciso" | "cto" | "junior_dev" | "solo_dev";

interface RoleContextType {
  role: UserRole;
  setRole: (role: UserRole) => void;
  roleName: string;
}

const RoleContext = createContext<RoleContextType | undefined>(undefined);

export function RoleProvider({ children }: { children: ReactNode }) {
  const [role, setRoleState] = useState<UserRole>("ciso");

  // Load from memory on component mount
  useEffect(() => {
    const savedRole = localStorage.getItem("plexus_role") as UserRole | null;
    if (savedRole) {
      setRoleState(savedRole);
    }
  }, []);

  // Update memory whenever role changes
  const setRole = (newRole: UserRole) => {
    setRoleState(newRole);
    localStorage.setItem("plexus_role", newRole);
  };

  const getRoleName = (r: UserRole) => {
    switch (r) {
      case "ciso":
        return "Chief Information Security Officer (CISO)";
      case "cto":
        return "Chief Technology Officer (CTO)";
      case "junior_dev":
        return "Junior Developer Onboarding";
      case "solo_dev":
        return "Solo Developer";
      default:
        return "Developer";
    }
  };

  return (
    <RoleContext.Provider value={{ role, setRole, roleName: getRoleName(role) }}>
      {children}
    </RoleContext.Provider>
  );
}

export function useRole() {
  const context = useContext(RoleContext);
  if (!context) {
    throw new Error("useRole must be used within a RoleProvider");
  }
  return context;
}
