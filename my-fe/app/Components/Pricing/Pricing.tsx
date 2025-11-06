import React from "react";
export const Pricing = () => {
  return (
    <div className="flex flex-col bg-white/90 items-center min-h-screen px-4 sm:px-6 lg:px-12 py-12 lg:py-20" id="pricing-section">
      <h1 className="text-2xl sm:text-3xl lg:text-4xl xl:text-5xl font-bold mb-8 lg:mb-12 text-center max-w-4xl">
        Choose the perfect plan to streamline your hiring process
      </h1>
      <div className="flex flex-col lg:flex-row gap-8 lg:gap-12 w-full max-w-6xl">
        {/* Basic Plan */}
        <div className="bg-black cursor-default w-full lg:w-1/2 p-6 lg:p-8 shadow-2xl text-white rounded-xl" id="pricing-card">
          <h2 className="text-2xl lg:text-3xl font-semibold mb-4">Basic</h2>
          <p className="text-4xl lg:text-5xl font-bold mb-6">
            FREE<span className="text-base font-normal"></span>
          </p>
          <ul className="mb-8 space-y-4 text-sm lg:text-base">
            <li>✔️ Access to Standard Resume template</li>
            <li>✔️ Tailor your resume for 3 times/day</li>
            <li>✔️ Apply upto 5 applications/day</li>
            <li>✔️ Limited access to Smart Applier</li>
          </ul>
          <button className="border border-white hover:bg-[#159950] w-full text-white font-bold py-3 px-4 rounded-lg focus:outline-none focus:shadow-outline hover:scale-105 transition-transform duration-300 cursor-pointer">
            Get started
          </button>
        </div>

        {/* Pro Plan */}
        <div className="price-card w-full lg:w-1/2 shadow-2xl border-2 border-[#FFFF00] cursor-pointer hover:border-[#FFD700] hover:border-4 transition-all duration-300 p-6 lg:p-8 text-black rounded-xl">
          <h2 className="text-2xl lg:text-3xl font-semibold mb-4">Pro</h2>
          <p className="text-4xl lg:text-5xl font-bold mb-6 text-black">
            ₹199<span className="text-base font-normal text-black">/month</span>
          </p>
          <ul className="mb-8 space-y-4 text-sm lg:text-base">
            <li>✔️ Access to all advanced resume templates</li>
            <li>✔️ Tailor your resume for 10 times/day</li>
            <li>✔️ Apply upto 20 applications/day</li>
            <li>✔️ Full access to Smart Applier</li>
          </ul>
          <button className="bg-black border hover:bg-gray-800 w-full text-white font-bold py-3 px-4 rounded-lg focus:outline-none focus:shadow-outline hover:scale-105 transition-transform duration-300 cursor-pointer">
            Choose plan
          </button>
        </div>
      </div>
    </div>
  );
};
