import React from "react";

const plans = [
  {
    name: "Starter",
    price: "FREE",
    period: "",
    description: "Perfect for exploring HireHawk's capabilities",
    features: [
      "Access to Standard Resume template",
      "Limited access to Tailoring (5 shared credits/day)",
      "Limited access to Portfolio (5 shared credits/day)",
      "Fetch jobs up to 2 times/day",
    ],
    cta: "Get Started",
    popular: false,
    link: "/register"
  },
  {
    name: "Pro",
    price: "₹199",
    period: "/month",
    description: "For serious job seekers who want maximum results",
    features: [
      "Access to all advanced resume templates",
      "Unlimited resume tailoring",
      "Unlimited portfolio building",
      "Unlimited job fetching",
      "Full access to Smart Applier",
      "Priority support",
    ],
    cta: "Upgrade to Pro",
    popular: true,
    link: "mailto:tejabudumuru3@gmail.com"
  },
];

export const Pricing = () => {
  return (
    <section className="py-24 px-5 lg:px-10 relative overflow-hidden" id="pricing-section">
      {/* Background glow */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[400px] bg-emerald-500/[0.04] rounded-full blur-[120px] pointer-events-none" />

      <div className="max-w-5xl mx-auto relative z-10">
        {/* Header */}
        <div className="text-center mb-16">
          <span className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-sm font-medium mb-6">
            Pricing
          </span>
          <h2 className="text-3xl lg:text-5xl font-bold gradient-text mb-4">
            Choose the perfect plan
          </h2>
          <p className="text-gray-400 text-lg max-w-xl mx-auto">
            Start free and upgrade when you&apos;re ready for more power.
          </p>
        </div>

        {/* Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 max-w-4xl mx-auto" id="pricing-card">
          {plans.map((plan) => (
            <div
              key={plan.name}
              className={`relative rounded-2xl p-8 transition-all duration-300 ${
                plan.popular
                  ? "bg-emerald-500 text-black shadow-2xl shadow-emerald-500/20 scale-[1.02]"
                  : "bg-[#1A1A1A] border border-white/[0.08] text-white hover:border-emerald-500/30"
              }`}
            >
              {/* Popular badge */}
              {plan.popular && (
                <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                  <span className="px-4 py-1 bg-black text-emerald-400 text-xs font-bold rounded-full uppercase tracking-wider">
                    Most Popular
                  </span>
                </div>
              )}

              <h3 className={`text-xl font-semibold mb-2 ${plan.popular ? "text-black" : "text-white"}`}>
                {plan.name}
              </h3>
              <p className={`text-sm mb-6 ${plan.popular ? "text-black/70" : "text-gray-400"}`}>
                {plan.description}
              </p>

              <div className="flex items-baseline gap-1 mb-8">
                <span className={`text-5xl font-bold ${plan.popular ? "text-black" : "text-white"}`}>
                  {plan.price}
                </span>
                {plan.period && (
                  <span className={`text-sm font-medium ${plan.popular ? "text-black/60" : "text-gray-500"}`}>
                    {plan.period}
                  </span>
                )}
              </div>

              <ul className="space-y-4 mb-8">
                {plan.features.map((feature) => (
                  <li key={feature} className="flex items-start gap-3">
                    <svg
                      className={`w-5 h-5 flex-shrink-0 mt-0.5 ${plan.popular ? "text-black" : "text-emerald-400"}`}
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                      strokeWidth={2}
                    >
                      <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                    </svg>
                    <span className={`text-sm ${plan.popular ? "text-black/80" : "text-gray-300"}`}>
                      {feature}
                    </span>
                  </li>
                ))}
              </ul>

              <a
                href={plan.link}
                className={`w-full block text-center py-3.5 px-6 rounded-xl font-semibold text-sm transition-all duration-300 cursor-pointer ${
                  plan.popular
                    ? "bg-black text-white hover:bg-gray-900 hover:shadow-lg"
                    : "bg-white/[0.05] border border-white/[0.1] text-white hover:bg-emerald-500 hover:text-black hover:border-emerald-500"
                }`}
              >
                {plan.cta}
              </a>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};
