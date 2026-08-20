import * as React from "react";
import { useNavigate, useLocation } from "react-router-dom";

export type NavSection = "security" | "code_quality" | "architecture" | "qa" | "system_health";

interface NavigationContextType {
  activeSection: NavSection;
  setActiveSection: (section: NavSection) => void;
  activeFindingsTab: string;
  setActiveFindingsTab: (tab: string) => void;
  highlightedAgent: string | null;
  setHighlightedAgent: (agentId: string | null) => void;
  navigateToSection: (section: NavSection) => void;
}

const NavigationContext = React.createContext<NavigationContextType | undefined>(undefined);

export function NavigationProvider({ children }: { children: React.ReactNode }) {
  const [activeSection, setActiveSection] = React.useState<NavSection>("security");
  const [activeFindingsTab, setActiveFindingsTab] = React.useState<string>("security");
  const [highlightedAgent, setHighlightedAgent] = React.useState<string | null>(null);

  const navigate = useNavigate();
  const location = useLocation();

  const navigateToSection = (section: NavSection) => {
    setActiveSection(section);

    // If not currently on a pull request page, navigate to the default PR review
    if (!location.pathname.startsWith("/pull-requests")) {
      navigate("/pull-requests/pr-142");
    }

    // Map sidebar sections to corresponding tabs & highlighted agents
    switch (section) {
      case "security":
        setActiveFindingsTab("security");
        setHighlightedAgent("security");
        break;
      case "code_quality":
        setHighlightedAgent("code_quality");
        break;
      case "architecture":
        setActiveFindingsTab("arch");
        setHighlightedAgent("architecture");
        break;
      case "qa":
        setActiveFindingsTab("qa");
        setHighlightedAgent("qa");
        break;
      case "system_health":
        setActiveFindingsTab("arch");
        setHighlightedAgent(null);
        break;
    }

    // Smooth scroll to the target DOM anchor
    setTimeout(() => {
      let targetId = `section-${section}`;
      if (section === "security") targetId = "section-security";
      else if (section === "code_quality") targetId = "section-code_quality";
      else if (section === "architecture" || section === "system_health") targetId = "section-architecture";
      else if (section === "qa") targetId = "section-qa";

      const element = document.getElementById(targetId);
      if (element) {
        element.scrollIntoView({ behavior: "smooth", block: "start" });
      }
    }, 100);
  };

  return (
    <NavigationContext.Provider
      value={{
        activeSection,
        setActiveSection,
        activeFindingsTab,
        setActiveFindingsTab,
        highlightedAgent,
        setHighlightedAgent,
        navigateToSection,
      }}
    >
      {children}
    </NavigationContext.Provider>
  );
}

export function useNavigation() {
  const context = React.useContext(NavigationContext);
  if (!context) {
    throw new Error("useNavigation must be used within a NavigationProvider");
  }
  return context;
}
