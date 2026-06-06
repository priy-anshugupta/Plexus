import { AbilityBuilder, createMongoAbility, MongoAbility } from "@casl/ability";

export type Action = "read" | "create" | "update" | "delete" | "manage";
export type Subject = "all" | "CisoDashboard" | "CtoDashboard" | "QuestDashboard" | "ComplianceMetrics" | "RiskScores" | "TechDebtCharts" | "SandboxQuests" | "RemediationPanel";

export type AppAbility = MongoAbility<[Action, Subject]>;

export function defineAbilityFor(role: string): AppAbility {
  const { can, cannot, build } = new AbilityBuilder<AppAbility>(createMongoAbility);

  if (role === "ciso") {
    // CISOs have full read access to security health, compliance metrics, and risk scores,
    // plus ability to run scans and view auto-fix remediation options.
    can("read", "CisoDashboard");
    can("read", "ComplianceMetrics");
    can("read", "RiskScores");
    can("read", "RemediationPanel");
    can("update", "RemediationPanel"); // approve auto-fixes
    cannot("read", "SandboxQuests");
    cannot("read", "TechDebtCharts");
  } else if (role === "cto") {
    // CTOs are concerned with development velocity, DORA metrics, tech debt graphs,
    // and overall high-level security score.
    can("read", "CtoDashboard");
    can("read", "TechDebtCharts");
    can("read", "RiskScores");
    cannot("read", "ComplianceMetrics");
    cannot("read", "SandboxQuests");
    cannot("read", "RemediationPanel");
  } else if (role === "junior_dev") {
    // Junior devs see the gamified onboarding quests, sandbox task cards, and basic dashboard.
    can("read", "QuestDashboard");
    can("read", "SandboxQuests");
    cannot("read", "ComplianceMetrics");
    cannot("read", "TechDebtCharts");
    cannot("read", "RemediationPanel");
  } else {
    // Fallback: guest or standard developer permissions
    can("read", "QuestDashboard");
  }

  return build();
}
