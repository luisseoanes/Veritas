import { HomeExperience } from "@/components/home/home-experience";
import { SiteBanner } from "@/components/layout/site-banner";

export default function HomePage() {
  return <HomeExperience banner={<SiteBanner />} />;
}
