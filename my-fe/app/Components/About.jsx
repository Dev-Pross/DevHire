import Image from "next/image";

const About = () => {
  return (
    <section className="py-24 px-5 lg:px-10 relative">
      {/* Background */}
      <div className="absolute bottom-0 left-0 w-[400px] h-[300px] bg-emerald-500/[0.04] rounded-full blur-[100px] pointer-events-none" />

      <div className="max-w-7xl mx-auto relative z-10">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 lg:gap-20 items-center">
          {/* Left — Image & Social */}
          <div className="flex flex-col items-center lg:items-start gap-8">
            <div className="relative group">
              <div className="absolute -inset-1 bg-gradient-to-r from-emerald-500/20 to-emerald-500/5 rounded-2xl blur-sm group-hover:blur-md transition-all duration-300" />
              <Image
                src="/full_logo.jpg"
                alt="HireHawk"
                width={400}
                height={500}
                className="relative rounded-2xl shadow-2xl shadow-black/50 object-cover border border-white/[0.06]"
              />
            </div>

            {/* Social Links */}
            <div>
              <h3 className="text-lg font-semibold text-white mb-4">Connect With Us</h3>
              <div className="flex gap-3">
                {[
                  {
                    href: "https://github.com/Dev-Pross/DevHire",
                    label: "GitHub",
                    icon: (
                      <path d="M12 0C5.374 0 0 5.373 0 12 0 17.302 3.438 21.8 8.207 23.387c.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23A11.509 11.509 0 0112 5.803c1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576C20.566 21.797 24 17.3 24 12c0-6.627-5.373-12-12-12z" />
                    ),
                  },
                  {
                    href: "https://linkedin.com/",
                    label: "LinkedIn",
                    icon: (
                      <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433a2.062 2.062 0 01-2.063-2.065 2.064 2.064 0 112.063 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z" />
                    ),
                  },
                  {
                    href: "https://x.com/",
                    label: "X/Twitter",
                    icon: (
                      <path d="M23.953 4.57a10 10 0 01-2.825.775 4.958 4.958 0 002.163-2.723c-.951.555-2.005.959-3.127 1.184a4.92 4.92 0 00-8.384 4.482C7.69 8.095 4.067 6.13 1.64 3.162a4.822 4.822 0 00-.666 2.475c0 1.71.87 3.213 2.188 4.096a4.904 4.904 0 01-2.228-.616v.06a4.923 4.923 0 003.946 4.827 4.996 4.996 0 01-2.212.085 4.936 4.936 0 004.604 3.417 9.867 9.867 0 01-6.102 2.105c-.39 0-.779-.023-1.17-.067a13.995 13.995 0 007.557 2.209c9.053 0 13.998-7.496 13.998-13.985 0-.21 0-.42-.015-.63A9.935 9.935 0 0024 4.59z" />
                    ),
                  },
                  {
                    href: "mailto:linkedinpostgenerator@gmail.com",
                    label: "Email",
                    icon: null,
                  },
                ].map((social) => (
                  <a
                    key={social.label}
                    href={social.href}
                    target="_blank"
                    rel="noopener noreferrer"
                    aria-label={social.label}
                    className="w-10 h-10 rounded-xl bg-white/[0.05] border border-white/[0.08] flex items-center justify-center text-gray-400 hover:text-emerald-400 hover:border-emerald-500/30 hover:bg-emerald-500/10 transition-all duration-300"
                  >
                    {social.icon ? (
                      <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
                        {social.icon}
                      </svg>
                    ) : (
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M3 8l7.89 4.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                      </svg>
                    )}
                  </a>
                ))}
              </div>
            </div>
          </div>

          {/* Right — Content */}
          <div className="space-y-8">
            <div>
              <span className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-sm font-medium mb-6">
                About Us
              </span>
              <h2 className="text-3xl lg:text-4xl font-bold text-white mb-4">
                About HireHawk
              </h2>
              <p className="text-gray-400 leading-relaxed">
                HireHawk is a cutting-edge platform designed to streamline the job search and application process for all professionals. We leverage AI to automate resume tailoring, job matching, and applications — so you can focus on what matters most: preparing for your dream role.
              </p>
            </div>

            <div>
              <h3 className="text-lg font-semibold text-white mb-4">What We Do</h3>
              <div className="grid grid-cols-2 gap-3">
                {[
                  { label: "Finding Jobs", color: "emerald" },
                  { label: "Tailoring Resumes", color: "emerald" },
                  { label: "Applying Efficiently", color: "emerald" },
                  { label: "Career Growth", color: "emerald" },
                ].map((tag) => (
                  <div
                    key={tag.label}
                    className="flex items-center gap-2.5 px-4 py-3 rounded-xl bg-white/[0.03] border border-white/[0.06] hover:border-emerald-500/20 transition-colors"
                  >
                    <div className="w-2 h-2 rounded-full bg-emerald-400" />
                    <span className="text-sm text-gray-300">{tag.label}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default About;
