import React from "react";
export const Pricing = () => {
  return (
    <div className="flex flex-col items-center justify-center min-h-screen  text-white">
      <h1 className="text-4xl font-bold mb-8">Pricing Plans</h1>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-8 w-full max-w-6xl px-4">
        <div className="bg-gray-800 p-6 rounded-lg shadow-lg">
          <h2 className="text-2xl font-semibold mb-4">Basic</h2>
          <p className="text-4xl font-bold mb-4">
            FREE<span className="text-base font-normal"></span>
          </p>
          <ul className="mb-6 space-y-2">
            <li>✔️ Access to basic features</li>
            <li>✔️ Email support</li>
            <li>✔️ Community access</li>
            <li> ✔️ Weeklu Webinars</li>
          </ul>
          <button className="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded hover:scale-105 transition-transform duration-300 cursor-pointer">
            Choose Basic
          </button>
        </div>
        <div className="bg-gray-800 p-6 rounded-lg shadow-lg border-2 border-blue-500">
          <h2 className="text-2xl font-semibold mb-4">Pro</h2>
          <p className="text-4xl font-bold mb-4">
            $30<span className="text-base font-normal">/month</span>
          </p>
          <ul className="mb-6 space-y-2">
            <li>✔️ All Basic features</li>
            <li>✔️ Priority email support</li>
            <li>✔️ Access to beta features</li>
            <li>✔️ Monthly webinars</li>
            <li>✔️ Discord access</li>
          </ul>
          <button className="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded hover:scale-105 transition-transform duration-300 cursor-pointer">
            Choose Pro
          </button>
        </div>
        <div className="bg-gray-800 p-6 rounded-lg shadow-lg">
          <h2 className="text-2xl font-semibold mb-4">Enterprise</h2>
          <p className="text-4xl font-bold mb-4">
            $100<span className="text-base font-normal">/month</span>
          </p>
          <ul className="mb-6 space-y-2">
            <li>✔️ All Pro features</li>
            <li>✔️ Dedicated account manager</li>
            <li>✔️ 24/7 phone support</li>
            <li>✔️ Custom integrations</li>
            <li>✔️ Discord access</li>
          </ul>
          <button className="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded hover:scale-105 transition-transform duration-300 cursor-pointer">
            Choose Enterprise
          </button>
        </div>
      </div>
    </div>
  );
};
