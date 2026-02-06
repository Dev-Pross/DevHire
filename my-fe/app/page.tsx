import Navbar from "./Components/Navbar";
import { HeroTalent } from "./Components/Landing-Page/hero-section";
import { Pricing } from "./Components/Pricing/Pricing";
import Features from "./Components/Features";
import About from "./Components/About";

export default async function Home() {
  return (
    <div className="min-h-screen">
      <Navbar />
      <HeroTalent />
      <Features />
      <Pricing />
      <About />
    </div>
  );
}
