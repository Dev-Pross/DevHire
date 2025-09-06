import React from "react";
export const Pricing = () => {
  return (
    <div className="flex bg-white/90 flex-col items-start  min-h-screen p-30" id="pricing-section">
      <h1 className="text-4xl font-bold mb-8 ">Choose the perfect plan to<br/> streamline your hiring process</h1>
      <div className="flex   w-full">
        <div className="bg-black cursor-default size-[70%] p-6 min-h-9/10 shadow-lg text-white">
          <h2 className="text-2xl font-semibold mb-4 ">Basic</h2>
          <p className="text-4xl font-bold mb-4">
            FREE<span className="text-base font-normal"></span>
          </p>
          <ul className="mb-6 space-y-5">
            <li>✔️ Access to Standard Resume template</li>
            <li>✔️ Tailor your resume for 3 times/day</li>
            <li>✔️ Apply upto 5 applications/day </li>
            <li>✔️ Limited access to Smart Applier</li>
          </ul>
          <button className="border border-white hover:bg-[#159950] w-full text-white font-bold py-2 px-4 rounded-4xl focus:outline-none focus:shadow-outline hover:scale-105 transition-transform duration-300 cursor-pointer">

            Get started
          </button>
        </div>

        <div className="price-card size-[70%] shadow-[-11px_0px_20px_1px_#ffffff30] border-[#FFFF00] cursor-pointer hover:border-[#FFD700] hover:border-2 transition-all duration-100 p-6 text-white animate-fade">
          <h2 className="text-2xl font-semibold mb-4">Pro</h2>
          <p className="text-4xl font-bold mb-4 text-[#00000]">
            199₹<span className="text-base font-normal text-black">/month</span>
          </p>
          <ul className="mb-6 space-y-5">
            <li>✔️ Access to all advanced resume templates</li>
            <li>✔️ Tailor your resume for 10 times/day</li>
            <li>✔️ Apply upto 20 applications/day</li>
            <li>✔️ Full access to Smart Applier</li>
          </ul>
          <button className="bg-black border hover:bg-gray w-full text-white font-bold py-2 px-4 rounded-4xl focus:outline-none focus:shadow-outline hover:scale-105 transition-transform duration-300 cursor-pointer">
            Choose plan
          </button>
        </div>
      </div>
    </div>
  );
};
