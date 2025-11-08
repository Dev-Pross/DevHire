// "use client";
// import { useEffect, useState } from "react";
import Navbar from "./Components/Navbar";
import { HeroTalent } from "./Components/Landing-Page/hero-section";
import { Pricing } from "./Components/Pricing/Pricing";
import Features from "./Components/Features";
import About from "./Components/About";

export default async  function Home() {
  return (
    <div>
      <Navbar />
      <div style={{ }}>

        <HeroTalent />
      </div>
      <Features/>
      <Pricing /> 
      <div className="w-full h-fit">
      <About/>
      </div>
    </div>
  );
}
