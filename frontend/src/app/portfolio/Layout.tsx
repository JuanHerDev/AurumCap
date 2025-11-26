// app/portfolio/layout.tsx
import { AuthChecker } from "@/components/AuthChecker";

export default function PortfolioLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <>
      <AuthChecker />
      {children}
    </>
  );
}