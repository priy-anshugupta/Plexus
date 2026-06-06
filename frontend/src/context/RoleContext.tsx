"use client";

import React, { createContext, useContext, useState, ReactNode } from "react";

export type UserRole = "ciso" | "cto" | "junior_dev";

interface RoleContextType {
  role: UserRole;
  setRole: (role: UserRole) => void;
  roleName: string;
}

const RoleContext = createContext<RoleContextType | undefined>(undefined);

export function RoleProvider({ children }: { children: ReactNode }) {
  const [role, setRole] = useState<UserRole>("ciso");

  const getRoleName = (r: UserRole) => {
    switch (r) {
      case "ciso":
        return "Chief Information Security Officer (CISO)";
      case "cto":
        return "Chief Technology Officer (CTO)";
      case "junior_dev":
        return "Junior Developer Onboarding";
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
