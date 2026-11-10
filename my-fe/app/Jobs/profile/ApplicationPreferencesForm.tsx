"use client";

import React, { useState, useEffect, useMemo } from "react";
import toast from "react-hot-toast";

export interface TargetCountryAuth {
  country: string;
  can_work_without_sponsorship: boolean;
  needs_sponsorship_now_or_future: boolean;
}

export interface ApplicationPreferences {
  is_complete: boolean;
  last_updated?: string;
  compensation: {
    expected_salary: number | "";
    currency: string;
    period: "yearly" | "monthly";
    salary_range_min?: number | "";
    salary_range_max?: number | "";
    current_salary?: number | "";
    prefer_not_to_say_current: boolean;
  };
  availability: {
    notice_period: "Immediate" | "15 days" | "30 days" | "60 days" | "90 days";
    notice_period_days: number;
    earliest_start_date?: string;
  };
  work_authorization: {
    citizenship: string;
    target_countries: TargetCountryAuth[];
    unlisted_country_action: "skip" | "apply_with_sponsorship_needed";
  };
  work_style: {
    willing_to_relocate: boolean;
    work_modes: Array<"Remote" | "Hybrid" | "Onsite">;
    preferred_locations: string[];
  };
  experience: {
    dates_found_in_resume: boolean;
    employment_years: number | "";
    hands_on_years: number | "";
  };
  target_domain: {
    domains: string[];
    custom_domains?: string;
    target_roles: string[];
  };
  demographics: {
    gender: "Prefer not to say" | "Male" | "Female" | "Non-Binary";
    disability_status: "Prefer not to say" | "No, I do not have a disability" | "Yes, I have a disability";
    veteran_status: "Prefer not to say" | "I am not a protected veteran" | "I identify as a protected veteran";
  };
}

const DEFAULT_PREFERENCES: ApplicationPreferences = {
  is_complete: false,
  compensation: {
    expected_salary: "",
    currency: "USD",
    period: "yearly",
    salary_range_min: "",
    salary_range_max: "",
    current_salary: "",
    prefer_not_to_say_current: false,
  },
  availability: {
    notice_period: "Immediate",
    notice_period_days: 0,
    earliest_start_date: "",
  },
  work_authorization: {
    citizenship: "India",
    target_countries: [
      { country: "India", can_work_without_sponsorship: true, needs_sponsorship_now_or_future: false },
      { country: "United States", can_work_without_sponsorship: false, needs_sponsorship_now_or_future: true },
    ],
    unlisted_country_action: "apply_with_sponsorship_needed",
  },
  work_style: {
    willing_to_relocate: true,
    work_modes: ["Remote", "Hybrid"],
    preferred_locations: [],
  },
  experience: {
    dates_found_in_resume: true,
    employment_years: "",
    hands_on_years: "",
  },
  target_domain: {
    domains: ["SaaS / Cloud", "AI / Machine Learning"],
    custom_domains: "",
    target_roles: ["Full Stack Engineer", "Software Engineer"],
  },
  demographics: {
    gender: "Prefer not to say",
    disability_status: "Prefer not to say",
    veteran_status: "Prefer not to say",
  },
};

const POPULAR_DOMAINS = [
  "Fintech",
  "HealthTech",
  "SaaS / Cloud",
  "AI / Machine Learning",
  "E-Commerce",
  "Cybersecurity",
  "EdTech",
  "Web3 / Blockchain",
  "Gaming",
  "DevOps & Cloud Infra",
  "Data & Analytics",
  "Enterprise Software",
];

const POPULAR_ROLES = [
  "Full Stack Engineer",
  "Backend Engineer",
  "Frontend Engineer",
  "Software Engineer",
  "DevOps Engineer",
  "AI / ML Engineer",
  "Mobile Developer",
];

const COMMON_COUNTRIES = [
  "India",
  "United States",
  "United Kingdom",
  "Canada",
  "Germany",
  "Netherlands",
  "Australia",
  "Singapore",
  "United Arab Emirates",
  "Ireland",
  "France",
  "Sweden",
  "Japan",
  "Switzerland",
];

const CURRENCIES = [
  { code: "USD", symbol: "$", label: "USD ($)" },
  { code: "INR", symbol: "₹", label: "INR (₹)" },
  { code: "EUR", symbol: "€", label: "EUR (€)" },
  { code: "GBP", symbol: "£", label: "GBP (£)" },
  { code: "CAD", symbol: "$", label: "CAD ($)" },
  { code: "AUD", symbol: "$", label: "AUD ($)" },
];

const NOTICE_PERIOD_OPTIONS: Array<{ label: ApplicationPreferences["availability"]["notice_period"]; days: number }> = [
  { label: "Immediate", days: 0 },
  { label: "15 days", days: 15 },
  { label: "30 days", days: 30 },
  { label: "60 days", days: 60 },
  { label: "90 days", days: 90 },
];

export const ApplicationPreferencesForm: React.FC<{
  userId: string;
  initialPreferences?: any;
  initialUserData?: any;
  onSaveSuccess?: (updated: ApplicationPreferences) => void;
}> = ({ userId, initialPreferences, initialUserData, onSaveSuccess }) => {
  const [formData, setFormData] = useState<ApplicationPreferences>(DEFAULT_PREFERENCES);
  const [isSaving, setIsSaving] = useState(false);
  const [newLocationInput, setNewLocationInput] = useState("");
  const [selectedCountryToAdd, setSelectedCountryToAdd] = useState("");
  const [showRangeFields, setShowRangeFields] = useState(false);
  const [customRoleInput, setCustomRoleInput] = useState("");

  // Initialize from props
  useEffect(() => {
    // Single Source of Truth for titles: candidate's user_data.titles takes precedence, fallback to preferences
    const candidateTitles: string[] =
      Array.isArray(initialUserData?.titles) && initialUserData.titles.length > 0
        ? initialUserData.titles
        : Array.isArray(initialPreferences?.target_domain?.target_roles) && initialPreferences.target_domain.target_roles.length > 0
        ? initialPreferences.target_domain.target_roles
        : DEFAULT_PREFERENCES.target_domain.target_roles;

    const safeTargetRoles = candidateTitles.slice(0, 5);

    if (initialPreferences && typeof initialPreferences === "object") {
      setFormData((prev) => ({
        ...prev,
        ...initialPreferences,
        compensation: { ...prev.compensation, ...(initialPreferences.compensation || {}) },
        availability: { ...prev.availability, ...(initialPreferences.availability || {}) },
        work_authorization: {
          ...prev.work_authorization,
          ...(initialPreferences.work_authorization || {}),
          target_countries: initialPreferences.work_authorization?.target_countries || prev.work_authorization.target_countries,
        },
        work_style: {
          ...prev.work_style,
          ...(initialPreferences.work_style || {}),
          work_modes: initialPreferences.work_style?.work_modes || prev.work_style.work_modes,
          preferred_locations: initialPreferences.work_style?.preferred_locations || prev.work_style.preferred_locations,
        },
        experience: { ...prev.experience, ...(initialPreferences.experience || {}) },
        target_domain: {
          domains: Array.isArray(initialPreferences.target_domain?.domains)
            ? initialPreferences.target_domain.domains
            : prev.target_domain.domains,
          custom_domains: initialPreferences.target_domain?.custom_domains || "",
          target_roles: safeTargetRoles,
        },
        demographics: { ...prev.demographics, ...(initialPreferences.demographics || {}) },
      }));

      if (initialPreferences.compensation?.salary_range_min || initialPreferences.compensation?.salary_range_max) {
        setShowRangeFields(true);
      }
    } else if (safeTargetRoles.length > 0) {
      setFormData((prev) => ({
        ...prev,
        target_domain: {
          ...prev.target_domain,
          target_roles: safeTargetRoles,
        },
      }));
    }
  }, [initialPreferences, initialUserData]);

  // Validation & completion calculation
  const validation = useMemo(() => {
    const checks = [
      { name: "Expected salary", valid: formData.compensation.expected_salary !== "" && Number(formData.compensation.expected_salary) > 0 },
      { name: "Notice period", valid: !!formData.availability.notice_period },
      { name: "Citizenship", valid: !!formData.work_authorization.citizenship },
      { name: "Target countries (at least 1)", valid: formData.work_authorization.target_countries.length > 0 },
      { name: "Work mode (at least 1)", valid: formData.work_style.work_modes.length > 0 },
      { name: "Employment experience", valid: formData.experience.employment_years !== "" && Number(formData.experience.employment_years) >= 0 },
      { name: "Hands-on experience", valid: formData.experience.hands_on_years !== "" && Number(formData.experience.hands_on_years) >= 0 },
    ];

    const completedCount = checks.filter((c) => c.valid).length;
    const percentage = Math.round((completedCount / checks.length) * 100);
    const missing = checks.filter((c) => !c.valid).map((c) => c.name);

    return { percentage, isComplete: percentage === 100, missing };
  }, [formData]);

  // Handler helpers
  const handleNoticeChange = (label: ApplicationPreferences["availability"]["notice_period"]) => {
    const found = NOTICE_PERIOD_OPTIONS.find((opt) => opt.label === label);
    setFormData((prev) => ({
      ...prev,
      availability: {
        ...prev.availability,
        notice_period: label,
        notice_period_days: found ? found.days : 0,
      },
    }));
  };

  const handleToggleDomain = (domain: string) => {
    setFormData((prev) => {
      const exists = prev.target_domain.domains.includes(domain);
      const updated = exists
        ? prev.target_domain.domains.filter((d) => d !== domain)
        : [...prev.target_domain.domains, domain];
      return {
        ...prev,
        target_domain: { ...prev.target_domain, domains: updated },
      };
    });
  };

  const handleToggleRole = (role: string) => {
    const isSelected = formData.target_domain.target_roles.includes(role);
    if (isSelected) {
      setFormData((prev) => ({
        ...prev,
        target_domain: {
          ...prev.target_domain,
          target_roles: prev.target_domain.target_roles.filter((r) => r !== role),
        },
      }));
      return;
    }

    if (formData.target_domain.target_roles.length >= 5) {
      toast.error("Maximum 5 target titles allowed. Remove one to add another.", {
        id: "max-titles-warning",
      });
      return;
    }

    setFormData((prev) => ({
      ...prev,
      target_domain: {
        ...prev.target_domain,
        target_roles: [...prev.target_domain.target_roles, role],
      },
    }));
  };

  const handleAddCustomRole = () => {
    const trimmed = customRoleInput.trim();
    if (!trimmed) return;
    if (formData.target_domain.target_roles.length >= 5) {
      toast.error("Maximum 5 target titles allowed. Remove one to add another.", {
        id: "max-titles-warning",
      });
      return;
    }
    const alreadyExists = formData.target_domain.target_roles.some(
      (r) => r.toLowerCase() === trimmed.toLowerCase()
    );
    if (alreadyExists) {
      toast.error(`"${trimmed}" is already added.`, { id: "duplicate-title-warning" });
      setCustomRoleInput("");
      return;
    }
    setFormData((prev) => ({
      ...prev,
      target_domain: {
        ...prev.target_domain,
        target_roles: [...prev.target_domain.target_roles, trimmed],
      },
    }));
    setCustomRoleInput("");
  };

  const handleRemoveRole = (roleToRemove: string) => {
    setFormData((prev) => ({
      ...prev,
      target_domain: {
        ...prev.target_domain,
        target_roles: prev.target_domain.target_roles.filter((r) => r !== roleToRemove),
      },
    }));
  };

  const handleToggleWorkMode = (mode: "Remote" | "Hybrid" | "Onsite") => {
    setFormData((prev) => {
      const exists = prev.work_style.work_modes.includes(mode);
      const updated = exists
        ? prev.work_style.work_modes.filter((m) => m !== mode)
        : [...prev.work_style.work_modes, mode];
      return {
        ...prev,
        work_style: { ...prev.work_style, work_modes: updated },
      };
    });
  };

  const handleAddLocation = () => {
    const loc = newLocationInput.trim();
    if (!loc) return;
    if (formData.work_style.preferred_locations.includes(loc)) {
      setNewLocationInput("");
      return;
    }
    setFormData((prev) => ({
      ...prev,
      work_style: {
        ...prev.work_style,
        preferred_locations: [...prev.work_style.preferred_locations, loc],
      },
    }));
    setNewLocationInput("");
  };

  const handleRemoveLocation = (loc: string) => {
    setFormData((prev) => ({
      ...prev,
      work_style: {
        ...prev.work_style,
        preferred_locations: prev.work_style.preferred_locations.filter((l) => l !== loc),
      },
    }));
  };

  const handleAddTargetCountry = () => {
    if (!selectedCountryToAdd) return;
    const exists = formData.work_authorization.target_countries.some((c) => c.country.toLowerCase() === selectedCountryToAdd.toLowerCase());
    if (exists) {
      toast.error(`${selectedCountryToAdd} is already in your target countries`);
      setSelectedCountryToAdd("");
      return;
    }

    const isSameAsCitizen = selectedCountryToAdd.toLowerCase() === formData.work_authorization.citizenship.toLowerCase();

    setFormData((prev) => ({
      ...prev,
      work_authorization: {
        ...prev.work_authorization,
        target_countries: [
          ...prev.work_authorization.target_countries,
          {
            country: selectedCountryToAdd,
            can_work_without_sponsorship: isSameAsCitizen,
            needs_sponsorship_now_or_future: !isSameAsCitizen,
          },
        ],
      },
    }));
    setSelectedCountryToAdd("");
  };

  const handleRemoveTargetCountry = (countryName: string) => {
    setFormData((prev) => ({
      ...prev,
      work_authorization: {
        ...prev.work_authorization,
        target_countries: prev.work_authorization.target_countries.filter((c) => c.country !== countryName),
      },
    }));
  };

  const handleCountryToggleChange = (countryName: string, field: "can_work_without_sponsorship" | "needs_sponsorship_now_or_future", val: boolean) => {
    setFormData((prev) => ({
      ...prev,
      work_authorization: {
        ...prev.work_authorization,
        target_countries: prev.work_authorization.target_countries.map((c) => {
          if (c.country === countryName) {
            return { ...c, [field]: val };
          }
          return c;
        }),
      },
    }));
  };

  const handleSave = async () => {
    if (!userId) {
      toast.error("User ID not available. Please refresh.");
      return;
    }

    setIsSaving(true);
    const loadToast = toast.loading("Saving application preferences...");

    const payload: ApplicationPreferences = {
      ...formData,
      is_complete: validation.isComplete,
      last_updated: new Date().toISOString(),
      compensation: {
        ...formData.compensation,
        expected_salary: formData.compensation.expected_salary === "" ? 0 : Number(formData.compensation.expected_salary),
        salary_range_min: formData.compensation.salary_range_min === "" ? undefined : Number(formData.compensation.salary_range_min),
        salary_range_max: formData.compensation.salary_range_max === "" ? undefined : Number(formData.compensation.salary_range_max),
        current_salary: formData.compensation.prefer_not_to_say_current
          ? ""
          : formData.compensation.current_salary === ""
            ? ""
            : Number(formData.compensation.current_salary),
      },
      experience: {
        ...formData.experience,
        employment_years: formData.experience.employment_years === "" ? 0 : Number(formData.experience.employment_years),
        hands_on_years: formData.experience.hands_on_years === "" ? 0 : Number(formData.experience.hands_on_years),
      },
      target_domain: {
        ...formData.target_domain,
        target_roles: formData.target_domain.target_roles.slice(0, 5),
      },
    };

    try {
      const res = await fetch("/api/User?action=patch_preferences", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          id: userId,
          preferences: payload,
          titles: payload.target_domain.target_roles,
        }),
      });

      const data = await res.json();
      if (res.ok && data.success) {
        toast.success(
          validation.isComplete
            ? "Preferences complete! 1-Click Auto Apply enabled."
            : "Preferences updated! Complete missing fields to unlock 1-Click Apply.",
          { id: loadToast, duration: 4000 }
        );
        if (onSaveSuccess) onSaveSuccess(payload);
      } else {
        toast.error(data.message || "Failed to save preferences", { id: loadToast });
      }
    } catch (err: any) {
      toast.error("Network error: " + err.message, { id: loadToast });
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="space-y-8 pb-28">
      {/* Header Info Banner */}
      <div className="p-4 sm:p-5 bg-gradient-to-r from-emerald-500/10 via-emerald-500/5 to-transparent border border-emerald-500/20 rounded-2xl flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse" />
            <h3 className="text-white font-semibold text-base sm:text-lg">Auto-Fill Profile</h3>
          </div>
          <p className="text-gray-400 text-xs sm:text-sm mt-1 max-w-xl">
            Configure your genuine job parameters once. HireHawk's auto-applier uses these authentic answers across all job boards, preventing screening rejections.
          </p>
        </div>
        <div className="flex items-center gap-2 flex-shrink-0 bg-[#121820] border border-white/[0.08] px-3.5 py-1.5 rounded-full">
          <span className="text-xs text-gray-400 font-medium">Profile Readiness:</span>
          <span
            className={`text-xs font-bold px-2 py-0.5 rounded-full ${validation.isComplete
              ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30"
              : "bg-amber-500/20 text-amber-400 border border-amber-500/30"
              }`}
          >
            {validation.percentage}%
          </span>
        </div>
      </div>

      {/* SECTION 1: COMPENSATION */}
      <div className="group p-5 sm:p-6 bg-white/[0.02] border border-white/[0.06] rounded-2xl hover:border-white/[0.1] transition-all duration-300 space-y-5">
        <div className="flex items-center justify-between border-b border-white/[0.06] pb-4">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400 font-bold text-sm">
              1
            </div>
            <div>
              <h4 className="text-white font-semibold text-base">Compensation & Salary Expectations</h4>
              <p className="text-xs text-gray-400">Used to accurately answer salary and CTC questions on application forms.</p>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-12 gap-4">
          {/* Expected Salary */}
          <div className="sm:col-span-6 space-y-1.5">
            <label className="text-xs font-medium text-gray-300">
              Expected Salary <span className="text-emerald-400">*</span>
            </label>
            <div className="relative flex items-center">
              <span className="absolute left-3.5 text-gray-400 font-medium text-sm">
                {CURRENCIES.find((c) => c.code === formData.compensation.currency)?.symbol || "$"}
              </span>
              <input
                type="number"
                placeholder="e.g. 85000"
                value={formData.compensation.expected_salary}
                onChange={(e) =>
                  setFormData((prev) => ({
                    ...prev,
                    compensation: { ...prev.compensation, expected_salary: e.target.value === "" ? "" : Number(e.target.value) },
                  }))
                }
                className="w-full bg-[#10141D] border border-white/[0.08] focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500/30 text-white rounded-xl pl-8 pr-4 py-2.5 text-sm transition-all outline-none"
              />
            </div>
          </div>

          {/* Currency Dropdown */}
          <div className="sm:col-span-3 space-y-1.5">
            <label className="text-xs font-medium text-gray-300">Currency</label>
            <select
              value={formData.compensation.currency}
              onChange={(e) =>
                setFormData((prev) => ({
                  ...prev,
                  compensation: { ...prev.compensation, currency: e.target.value },
                }))
              }
              className="w-full bg-[#10141D] border border-white/[0.08] focus:border-emerald-500 text-white rounded-xl px-3 py-2.5 text-sm transition-all outline-none cursor-pointer"
            >
              {CURRENCIES.map((cur) => (
                <option key={cur.code} value={cur.code} className="bg-[#121820] text-white">
                  {cur.label}
                </option>
              ))}
            </select>
          </div>

          {/* Period Toggle */}
          <div className="sm:col-span-3 space-y-1.5">
            <label className="text-xs font-medium text-gray-300">Period</label>
            <div className="grid grid-cols-2 bg-[#10141D] border border-white/[0.08] rounded-xl p-1">
              <button
                type="button"
                onClick={() =>
                  setFormData((prev) => ({
                    ...prev,
                    compensation: { ...prev.compensation, period: "yearly" },
                  }))
                }
                className={`py-1.5 text-xs font-medium rounded-lg transition-all ${formData.compensation.period === "yearly"
                  ? "bg-emerald-500 text-black font-semibold shadow"
                  : "text-gray-400 hover:text-white"
                  }`}
              >
                Yearly
              </button>
              <button
                type="button"
                onClick={() =>
                  setFormData((prev) => ({
                    ...prev,
                    compensation: { ...prev.compensation, period: "monthly" },
                  }))
                }
                className={`py-1.5 text-xs font-medium rounded-lg transition-all ${formData.compensation.period === "monthly"
                  ? "bg-emerald-500 text-black font-semibold shadow"
                  : "text-gray-400 hover:text-white"
                  }`}
              >
                Monthly
              </button>
            </div>
          </div>
        </div>

        {/* Current Salary + Range toggle */}
        <div className="pt-2 border-t border-white/[0.04] grid grid-cols-1 sm:grid-cols-12 gap-4 items-center">
          <div className="sm:col-span-6 space-y-1.5">
            <div className="flex items-center justify-between">
              <label className="text-xs font-medium text-gray-300">Current Salary / CTC</label>
              <label className="flex items-center gap-1.5 cursor-pointer text-xs text-gray-400 hover:text-gray-300">
                <input
                  type="checkbox"
                  checked={formData.compensation.prefer_not_to_say_current}
                  onChange={(e) =>
                    setFormData((prev) => ({
                      ...prev,
                      compensation: { ...prev.compensation, prefer_not_to_say_current: e.target.checked },
                    }))
                  }
                  className="rounded border-white/[0.1] text-emerald-500 focus:ring-0 bg-[#10141D]"
                />
                Prefer not to say
              </label>
            </div>
            {!formData.compensation.prefer_not_to_say_current && (
              <input
                type="number"
                placeholder="Current CTC (leave blank if fresher)"
                value={formData.compensation.current_salary ?? ""}
                onChange={(e) =>
                  setFormData((prev) => ({
                    ...prev,
                    compensation: { ...prev.compensation, current_salary: e.target.value === "" ? "" : Number(e.target.value) },
                  }))
                }
                className="w-full bg-[#10141D] border border-white/[0.08] focus:border-emerald-500 text-white rounded-xl px-4 py-2.5 text-sm outline-none"
              />
            )}
          </div>

          <div className="sm:col-span-6 sm:pt-4">
            <button
              type="button"
              onClick={() => setShowRangeFields(!showRangeFields)}
              className="text-xs text-emerald-400 hover:text-emerald-300 font-medium flex items-center gap-1.5 transition-colors"
            >
              <span>{showRangeFields ? "− Hide salary range (min/max)" : "+ Specify minimum & maximum range"}</span>
            </button>
          </div>
        </div>

        {showRangeFields && (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2">
            <div className="space-y-1.5">
              <label className="text-xs text-gray-400">Minimum Acceptable Salary (Optional)</label>
              <input
                type="number"
                placeholder="e.g. 75000"
                value={formData.compensation.salary_range_min}
                onChange={(e) =>
                  setFormData((prev) => ({
                    ...prev,
                    compensation: { ...prev.compensation, salary_range_min: e.target.value === "" ? "" : Number(e.target.value) },
                  }))
                }
                className="w-full bg-[#10141D] border border-white/[0.08] focus:border-emerald-500 text-white rounded-xl px-4 py-2 text-sm outline-none"
              />
            </div>
            <div className="space-y-1.5">
              <label className="text-xs text-gray-400">Maximum Desired Salary (Optional)</label>
              <input
                type="number"
                placeholder="e.g. 100000"
                value={formData.compensation.salary_range_max}
                onChange={(e) =>
                  setFormData((prev) => ({
                    ...prev,
                    compensation: { ...prev.compensation, salary_range_max: e.target.value === "" ? "" : Number(e.target.value) },
                  }))
                }
                className="w-full bg-[#10141D] border border-white/[0.08] focus:border-emerald-500 text-white rounded-xl px-4 py-2 text-sm outline-none"
              />
            </div>
          </div>
        )}
      </div>

      {/* SECTION 2: AVAILABILITY & NOTICE PERIOD */}
      <div className="group p-5 sm:p-6 bg-white/[0.02] border border-white/[0.06] rounded-2xl hover:border-white/[0.1] transition-all duration-300 space-y-5">
        <div className="flex items-center justify-between border-b border-white/[0.06] pb-4">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400 font-bold text-sm">
              2
            </div>
            <div>
              <h4 className="text-white font-semibold text-base">Notice Period & Availability</h4>
              <p className="text-xs text-gray-400">Accurately answers notice duration and earliest start date inquiries.</p>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {/* Notice Period */}
          <div className="space-y-1.5">
            <label className="text-xs font-medium text-gray-300">
              Notice Period <span className="text-emerald-400">*</span>
            </label>
            <div className="grid grid-cols-3 sm:grid-cols-5 gap-2">
              {NOTICE_PERIOD_OPTIONS.map((opt) => (
                <button
                  key={opt.label}
                  type="button"
                  onClick={() => handleNoticeChange(opt.label)}
                  className={`py-2 px-2 text-xs font-medium rounded-xl border text-center transition-all ${formData.availability.notice_period === opt.label
                    ? "bg-emerald-500/20 border-emerald-500 text-emerald-300 font-semibold"
                    : "bg-[#10141D] border-white/[0.08] text-gray-400 hover:text-white hover:border-white/[0.2]"
                    }`}
                >
                  {opt.label}
                </button>
              ))}
            </div>
          </div>

          {/* Earliest Start Date */}
          <div className="space-y-1.5">
            <label className="text-xs font-medium text-gray-300">Earliest Start Date (Optional)</label>
            <input
              type="date"
              value={formData.availability.earliest_start_date || ""}
              onChange={(e) =>
                setFormData((prev) => ({
                  ...prev,
                  availability: { ...prev.availability, earliest_start_date: e.target.value },
                }))
              }
              className="w-full bg-[#10141D] border border-white/[0.08] focus:border-emerald-500 text-white rounded-xl px-4 py-2 text-sm outline-none"
            />
          </div>
        </div>
      </div>

      {/* SECTION 3: WORK AUTHORIZATION & COUNTRY MATRIX */}
      <div className="group p-5 sm:p-6 bg-white/[0.02] border border-white/[0.06] rounded-2xl hover:border-white/[0.1] transition-all duration-300 space-y-5">
        <div className="flex items-center justify-between border-b border-white/[0.06] pb-4">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400 font-bold text-sm">
              3
            </div>
            <div>
              <h4 className="text-white font-semibold text-base">Work Authorization & Global Sponsorship Matrix</h4>
              <p className="text-xs text-gray-400">Match against the job location country to prevent visa mismatch rejections.</p>
            </div>
          </div>
        </div>

        {/* Citizenship Selection */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 items-center">
          <div className="space-y-1.5">
            <label className="text-xs font-medium text-gray-300">
              Primary Citizenship <span className="text-emerald-400">*</span>
            </label>
            <select
              value={formData.work_authorization.citizenship}
              onChange={(e) => {
                const newCitizen = e.target.value;
                setFormData((prev) => ({
                  ...prev,
                  work_authorization: {
                    ...prev.work_authorization,
                    citizenship: newCitizen,
                  },
                }));
              }}
              className="w-full bg-[#10141D] border border-white/[0.08] focus:border-emerald-500 text-white rounded-xl px-3.5 py-2.5 text-sm outline-none cursor-pointer"
            >
              {COMMON_COUNTRIES.map((country) => (
                <option key={country} value={country} className="bg-[#121820] text-white">
                  {country}
                </option>
              ))}
            </select>
          </div>

          <div className="space-y-1.5">
            <label className="text-xs font-medium text-gray-300">Add Target Country to Matrix</label>
            <div className="flex gap-2">
              <select
                value={selectedCountryToAdd}
                onChange={(e) => setSelectedCountryToAdd(e.target.value)}
                className="flex-1 bg-[#10141D] border border-white/[0.08] focus:border-emerald-500 text-white rounded-xl px-3.5 py-2 text-sm outline-none cursor-pointer"
              >
                <option value="">Select country...</option>
                {COMMON_COUNTRIES.filter(
                  (c) => !formData.work_authorization.target_countries.some((tc) => tc.country.toLowerCase() === c.toLowerCase())
                ).map((c) => (
                  <option key={c} value={c} className="bg-[#121820] text-white">
                    {c}
                  </option>
                ))}
              </select>
              <button
                type="button"
                onClick={handleAddTargetCountry}
                disabled={!selectedCountryToAdd}
                className="bg-emerald-500 hover:bg-emerald-400 disabled:opacity-40 text-black font-semibold text-xs px-4 py-2 rounded-xl transition-all"
              >
                + Add
              </button>
            </div>
          </div>
        </div>

        {/* Matrix Cards */}
        <div className="space-y-3 pt-2">
          <label className="text-xs font-medium text-gray-300">Configured Country Rights ({formData.work_authorization.target_countries.length})</label>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {formData.work_authorization.target_countries.map((item) => (
              <div
                key={item.country}
                className="p-4 bg-[#10141D] border border-white/[0.08] rounded-xl space-y-3 relative group/item"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="font-semibold text-white text-sm">{item.country}</span>
                    {item.country.toLowerCase() === formData.work_authorization.citizenship.toLowerCase() && (
                      <span className="text-[10px] bg-emerald-500/20 text-emerald-300 px-2 py-0.5 rounded-full border border-emerald-500/30">
                        Citizen
                      </span>
                    )}
                  </div>
                  <button
                    type="button"
                    onClick={() => handleRemoveTargetCountry(item.country)}
                    className="text-gray-500 hover:text-red-400 text-xs transition-colors p-1"
                    title="Remove country"
                  >
                    ✕
                  </button>
                </div>

                <div className="space-y-2 pt-1 border-t border-white/[0.04]">
                  {/* Can work without sponsorship */}
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-gray-300">Authorized without visa sponsorship?</span>
                    <button
                      type="button"
                      onClick={() => handleCountryToggleChange(item.country, "can_work_without_sponsorship", !item.can_work_without_sponsorship)}
                      className={`px-2.5 py-1 rounded-lg font-medium transition-all ${item.can_work_without_sponsorship
                        ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/30"
                        : "bg-red-500/10 text-red-300 border border-red-500/20"
                        }`}
                    >
                      {item.can_work_without_sponsorship ? "Yes" : "No"}
                    </button>
                  </div>

                  {/* Needs sponsorship */}
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-gray-300">Require visa sponsorship?</span>
                    <button
                      type="button"
                      onClick={() => handleCountryToggleChange(item.country, "needs_sponsorship_now_or_future", !item.needs_sponsorship_now_or_future)}
                      className={`px-2.5 py-1 rounded-lg font-medium transition-all ${item.needs_sponsorship_now_or_future
                        ? "bg-amber-500/20 text-amber-300 border border-amber-500/30"
                        : "bg-white/[0.05] text-gray-400 border border-white/[0.08]"
                        }`}
                    >
                      {item.needs_sponsorship_now_or_future ? "Yes (Sponsorship needed)" : "No"}
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Unlisted Country Policy */}
        <div className="p-3.5 bg-[#10141D]/60 border border-white/[0.06] rounded-xl flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 text-xs">
          <span className="text-gray-400">If a job is located in an unlisted country:</span>
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() =>
                setFormData((prev) => ({
                  ...prev,
                  work_authorization: { ...prev.work_authorization, unlisted_country_action: "skip" },
                }))
              }
              className={`px-3 py-1.5 rounded-lg transition-all ${formData.work_authorization.unlisted_country_action === "skip"
                ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 font-medium"
                : "bg-white/[0.03] text-gray-400 hover:text-white"
                }`}
            >
              Skip application
            </button>
            <button
              type="button"
              onClick={() =>
                setFormData((prev) => ({
                  ...prev,
                  work_authorization: { ...prev.work_authorization, unlisted_country_action: "apply_with_sponsorship_needed" },
                }))
              }
              className={`px-3 py-1.5 rounded-lg transition-all ${formData.work_authorization.unlisted_country_action === "apply_with_sponsorship_needed"
                ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 font-medium"
                : "bg-white/[0.03] text-gray-400 hover:text-white"
                }`}
            >
              Apply declaring sponsorship needed
            </button>
          </div>
        </div>
      </div>

      {/* SECTION 4: WORK STYLE & RELOCATION */}
      <div className="group p-5 sm:p-6 bg-white/[0.02] border border-white/[0.06] rounded-2xl hover:border-white/[0.1] transition-all duration-300 space-y-5">
        <div className="flex items-center justify-between border-b border-white/[0.06] pb-4">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400 font-bold text-sm">
              4
            </div>
            <div>
              <h4 className="text-white font-semibold text-base">Work Mode & Relocation Preferences</h4>
              <p className="text-xs text-gray-400">Controls remote, hybrid, onsite, and relocation form questions.</p>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {/* Relocation */}
          <div className="p-4 bg-[#10141D] border border-white/[0.08] rounded-xl flex items-center justify-between">
            <div>
              <span className="text-xs font-semibold text-white block">Willing to relocate?</span>
              <span className="text-[11px] text-gray-400">Answers relocation confirmation questions</span>
            </div>
            <button
              type="button"
              onClick={() =>
                setFormData((prev) => ({
                  ...prev,
                  work_style: { ...prev.work_style, willing_to_relocate: !prev.work_style.willing_to_relocate },
                }))
              }
              className={`px-3 py-1 rounded-lg text-xs font-semibold transition-all ${formData.work_style.willing_to_relocate
                ? "bg-emerald-500 text-black"
                : "bg-white/[0.08] text-gray-400"
                }`}
            >
              {formData.work_style.willing_to_relocate ? "Yes" : "No"}
            </button>
          </div>

          {/* Work Modes */}
          <div className="p-4 bg-[#10141D] border border-white/[0.08] rounded-xl space-y-2">
            <span className="text-xs font-semibold text-white block">Preferred Work Modes (select all that apply)</span>
            <div className="flex items-center gap-2">
              {(["Remote", "Hybrid", "Onsite"] as const).map((mode) => {
                const active = formData.work_style.work_modes.includes(mode);
                return (
                  <button
                    key={mode}
                    type="button"
                    onClick={() => handleToggleWorkMode(mode)}
                    className={`flex-1 py-1.5 text-xs font-medium rounded-lg border transition-all ${active
                      ? "bg-emerald-500/20 border-emerald-500 text-emerald-300 font-semibold"
                      : "bg-white/[0.03] border-white/[0.08] text-gray-400 hover:text-white"
                      }`}
                  >
                    {mode}
                  </button>
                );
              })}
            </div>
          </div>
        </div>

        {/* Preferred Locations */}
        <div className="space-y-2">
          <label className="text-xs font-medium text-gray-300">Preferred Locations / Cities (Optional)</label>
          <div className="flex gap-2">
            <input
              type="text"
              placeholder="e.g. Bengaluru, Hyderabad, San Francisco, London"
              value={newLocationInput}
              onChange={(e) => setNewLocationInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") {
                  e.preventDefault();
                  handleAddLocation();
                }
              }}
              className="flex-1 bg-[#10141D] border border-white/[0.08] focus:border-emerald-500 text-white rounded-xl px-4 py-2 text-sm outline-none"
            />
            <button
              type="button"
              onClick={handleAddLocation}
              className="bg-white/[0.08] hover:bg-white/[0.15] text-white text-xs font-semibold px-4 py-2 rounded-xl transition-all"
            >
              + Add
            </button>
          </div>
          {formData.work_style.preferred_locations.length > 0 && (
            <div className="flex flex-wrap gap-1.5 pt-1">
              {formData.work_style.preferred_locations.map((loc) => (
                <span
                  key={loc}
                  className="bg-[#10141D] border border-white/[0.08] text-gray-300 text-xs px-2.5 py-1 rounded-full flex items-center gap-1.5"
                >
                  {loc}
                  <button
                    type="button"
                    onClick={() => handleRemoveLocation(loc)}
                    className="text-gray-500 hover:text-red-400 text-xs"
                  >
                    ✕
                  </button>
                </span>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* SECTION 5: 2-WAY EXPERIENCE */}
      <div className="group p-5 sm:p-6 bg-white/[0.02] border border-white/[0.06] rounded-2xl hover:border-white/[0.1] transition-all duration-300 space-y-5">
        <div className="flex items-center justify-between border-b border-white/[0.06] pb-4">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400 font-bold text-sm">
              5
            </div>
            <div>
              <h4 className="text-white font-semibold text-base">2-Way Experience Engine (Employment vs Hands-on)</h4>
              <p className="text-xs text-gray-400">Intelligently classifies ATS experience questions to avoid instant rejection.</p>
            </div>
          </div>
        </div>

        {/* Informational Guidance */}
        <div className="p-3.5 bg-emerald-500/5 border border-emerald-500/15 rounded-xl text-xs text-gray-300 space-y-1">
          <p className="font-semibold text-emerald-400">💡 How Experience Classification Works:</p>
          <ul className="list-disc list-inside space-y-0.5 text-gray-400">
            <li>
              <strong className="text-gray-200">Employment Experience</strong>: Formal corporate/payroll tenure. Freshers & students enter{" "}
              <strong className="text-emerald-400">0</strong>.
            </li>
            <li>
              <strong className="text-gray-200">Hands-on Experience</strong>: Total practical coding duration (projects, internships, freelance, self-built apps).
            </li>
            <li>
              <span className="text-gray-300">Skill questions</span> (e.g. <em>"Years of React/Python?"</em>) automatically use your hands-on experience number.
            </li>
          </ul>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {/* Employment Years */}
          <div className="space-y-1.5">
            <label className="text-xs font-medium text-gray-300">
              Employment / Corporate Experience (Years) <span className="text-emerald-400">*</span>
            </label>
            <input
              type="number"
              step="0.5"
              min="0"
              placeholder="0 for freshers, or company tenure"
              value={formData.experience.employment_years}
              onChange={(e) =>
                setFormData((prev) => ({
                  ...prev,
                  experience: { ...prev.experience, employment_years: e.target.value === "" ? "" : Number(e.target.value) },
                }))
              }
              className="w-full bg-[#10141D] border border-white/[0.08] focus:border-emerald-500 text-white rounded-xl px-4 py-2.5 text-sm outline-none"
            />
            <span className="text-[11px] text-gray-500">Enter 0 if entry-level or student</span>
          </div>

          {/* Hands-on Years */}
          <div className="space-y-1.5">
            <label className="text-xs font-medium text-gray-300">
              Hands-on / Software / Project Experience (Years) <span className="text-emerald-400">*</span>
            </label>
            <input
              type="number"
              step="0.5"
              min="0"
              placeholder="e.g. 1.5, 2, 3"
              value={formData.experience.hands_on_years}
              onChange={(e) =>
                setFormData((prev) => ({
                  ...prev,
                  experience: { ...prev.experience, hands_on_years: e.target.value === "" ? "" : Number(e.target.value) },
                }))
              }
              className="w-full bg-[#10141D] border border-white/[0.08] focus:border-emerald-500 text-white rounded-xl px-4 py-2.5 text-sm outline-none"
            />
            <span className="text-[11px] text-gray-500">Duration spent actively building software & tools</span>
          </div>
        </div>
      </div>

      {/* SECTION 6: TARGET DOMAINS & ROLES */}
      <div className="group p-5 sm:p-6 bg-white/[0.02] border border-white/[0.06] rounded-2xl hover:border-white/[0.1] transition-all duration-300 space-y-5">
        <div className="flex items-center justify-between border-b border-white/[0.06] pb-4">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400 font-bold text-sm">
              6
            </div>
            <div>
              <h4 className="text-white font-semibold text-base">Target Domains & Functional Roles</h4>
              <p className="text-xs text-gray-400">Specify the industry domains and engineering roles you want to target in applications.</p>
            </div>
          </div>
        </div>

        <div className="space-y-4">
          {/* Target Domains */}
          <div className="space-y-2">
            <label className="text-xs font-medium text-gray-300">
              Preferred Domains & Industries <span className="text-gray-500 text-[11px]">(Click to select/unselect)</span>
            </label>
            <div className="flex flex-wrap gap-2">
              {POPULAR_DOMAINS.map((domain) => {
                const isSelected = formData.target_domain.domains.includes(domain);
                return (
                  <button
                    key={domain}
                    type="button"
                    onClick={() => handleToggleDomain(domain)}
                    className={`px-3 py-1.5 rounded-lg text-xs font-medium border transition-all duration-200 ${
                      isSelected
                        ? "bg-emerald-500/20 text-emerald-400 border-emerald-500/40 shadow-sm shadow-emerald-500/10"
                        : "bg-white/[0.03] text-gray-400 border-white/[0.08] hover:text-white hover:border-white/[0.15]"
                    }`}
                  >
                    {isSelected && <span className="mr-1.5">✓</span>}
                    {domain}
                  </button>
                );
              })}
            </div>
          </div>

          {/* Custom Domains text input */}
          <div className="space-y-1.5">
            <label className="text-xs font-medium text-gray-300">
              Other Domains / Sectors <span className="text-gray-500 text-[11px]">(Optional, comma-separated)</span>
            </label>
            <input
              type="text"
              value={formData.target_domain.custom_domains || ""}
              onChange={(e) =>
                setFormData((prev) => ({
                  ...prev,
                  target_domain: { ...prev.target_domain, custom_domains: e.target.value },
                }))
              }
              placeholder="e.g. Logistics, AdTech, TravelTech, CleanTech"
              className="w-full bg-[#10141D] border border-white/[0.08] focus:border-emerald-500 text-white rounded-xl px-3.5 py-2 text-sm outline-none"
            />
          </div>

          {/* Target Roles */}
          <div className="space-y-3 pt-2">
            <div className="flex items-center justify-between">
              <label className="text-xs font-semibold text-gray-200 flex items-center gap-2">
                <span>Target Job Titles</span>
                <span className="text-[11px] font-normal text-gray-400">(Used by Scraper & Auto-Apply Bot)</span>
              </label>
              <span
                className={`text-xs px-2.5 py-0.5 rounded-full font-semibold border ${
                  formData.target_domain.target_roles.length === 5
                    ? "bg-amber-500/15 text-amber-300 border-amber-500/30"
                    : formData.target_domain.target_roles.length > 0
                    ? "bg-emerald-500/15 text-emerald-300 border-emerald-500/30"
                    : "bg-white/[0.05] text-gray-400 border-white/[0.1]"
                }`}
              >
                {formData.target_domain.target_roles.length} / 5 selected
              </span>
            </div>

            {/* Active Selected Titles Chips */}
            <div className="flex flex-wrap gap-2 min-h-[44px] p-2.5 bg-[#0B0F17] border border-white/[0.08] rounded-xl items-center">
              {formData.target_domain.target_roles.length === 0 ? (
                <span className="text-xs text-gray-500 italic pl-1">
                  No target titles selected. Add up to 5 titles below to drive your job scraper.
                </span>
              ) : (
                formData.target_domain.target_roles.map((role) => (
                  <span
                    key={role}
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-emerald-500/15 text-emerald-300 border border-emerald-500/30 shadow-sm shadow-emerald-500/10 group"
                  >
                    <span>{role}</span>
                    <button
                      type="button"
                      onClick={() => handleRemoveRole(role)}
                      className="text-emerald-400 hover:text-red-400 hover:bg-white/10 rounded p-0.5 transition-colors cursor-pointer"
                      title={`Remove ${role}`}
                    >
                      ✕
                    </button>
                  </span>
                ))
              )}
            </div>

            {/* Custom Title Input Box */}
            <div className="flex gap-2">
              <input
                type="text"
                value={customRoleInput}
                onChange={(e) => setCustomRoleInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") {
                    e.preventDefault();
                    handleAddCustomRole();
                  }
                }}
                disabled={formData.target_domain.target_roles.length >= 5}
                placeholder={
                  formData.target_domain.target_roles.length >= 5
                    ? "Maximum 5 titles reached. Remove one to add a new title."
                    : "Type a custom job title (e.g. MERN Full Stack Developer, Python Engineer)..."
                }
                className="flex-1 bg-[#10141D] border border-white/[0.08] focus:border-emerald-500 disabled:opacity-50 disabled:cursor-not-allowed text-white rounded-xl px-3.5 py-2 text-sm outline-none transition-all placeholder:text-gray-500"
              />
              <button
                type="button"
                onClick={handleAddCustomRole}
                disabled={formData.target_domain.target_roles.length >= 5 || !customRoleInput.trim()}
                className="bg-emerald-500 hover:bg-emerald-400 disabled:opacity-40 disabled:hover:bg-emerald-500 text-black font-semibold text-xs px-4 py-2 rounded-xl transition-all shadow-md shadow-emerald-500/10 cursor-pointer disabled:cursor-not-allowed"
              >
                + Add Title
              </button>
            </div>

            {/* Quick-Add Suggestions from Popular Roles */}
            <div className="space-y-1.5 pt-1">
              <div className="flex items-center justify-between">
                <span className="text-[11px] font-medium text-gray-400">Quick-Add Popular Titles:</span>
                <span className="text-[10px] text-gray-500">Click to toggle (max 5)</span>
              </div>
              <div className="flex flex-wrap gap-1.5">
                {POPULAR_ROLES.map((role) => {
                  const isSelected = formData.target_domain.target_roles.includes(role);
                  return (
                    <button
                      key={role}
                      type="button"
                      onClick={() => handleToggleRole(role)}
                      className={`px-2.5 py-1 rounded-md text-[11px] font-medium border transition-all duration-200 ${
                        isSelected
                          ? "bg-emerald-500/20 text-emerald-400 border-emerald-500/40"
                          : "bg-white/[0.03] text-gray-400 border-white/[0.06] hover:text-white hover:border-white/[0.12]"
                      }`}
                    >
                      {isSelected ? "✓ " : "+ "}
                      {role}
                    </button>
                  );
                })}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* SECTION 7: EQUAL OPPORTUNITY & DEMOGRAPHICS */}
      <div className="group p-5 sm:p-6 bg-white/[0.02] border border-white/[0.06] rounded-2xl hover:border-white/[0.1] transition-all duration-300 space-y-5">
        <div className="flex items-center justify-between border-b border-white/[0.06] pb-4">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400 font-bold text-sm">
              7
            </div>
            <div>
              <h4 className="text-white font-semibold text-base">Equal Opportunity & Demographics Defaults</h4>
              <p className="text-xs text-gray-400">Default answers for standard voluntary surveys. Defaults to &quot;Prefer not to say&quot;.</p>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          {/* Gender */}
          <div className="space-y-1.5">
            <label className="text-xs font-medium text-gray-300">Gender</label>
            <select
              value={formData.demographics.gender}
              onChange={(e) =>
                setFormData((prev) => ({
                  ...prev,
                  demographics: { ...prev.demographics, gender: e.target.value as any },
                }))
              }
              className="w-full bg-[#10141D] border border-white/[0.08] focus:border-emerald-500 text-white rounded-xl px-3 py-2 text-sm outline-none cursor-pointer"
            >
              <option value="Prefer not to say" className="bg-[#121820]">Prefer not to say</option>
              <option value="Male" className="bg-[#121820]">Male</option>
              <option value="Female" className="bg-[#121820]">Female</option>
              <option value="Non-Binary" className="bg-[#121820]">Non-Binary</option>
            </select>
          </div>

          {/* Disability */}
          <div className="space-y-1.5">
            <label className="text-xs font-medium text-gray-300">Disability Status</label>
            <select
              value={formData.demographics.disability_status}
              onChange={(e) =>
                setFormData((prev) => ({
                  ...prev,
                  demographics: { ...prev.demographics, disability_status: e.target.value as any },
                }))
              }
              className="w-full bg-[#10141D] border border-white/[0.08] focus:border-emerald-500 text-white rounded-xl px-3 py-2 text-sm outline-none cursor-pointer"
            >
              <option value="Prefer not to say" className="bg-[#121820]">Prefer not to say</option>
              <option value="No, I do not have a disability" className="bg-[#121820]">No disability</option>
              <option value="Yes, I have a disability" className="bg-[#121820]">Yes, I have a disability</option>
            </select>
          </div>

          {/* Veteran */}
          <div className="space-y-1.5">
            <label className="text-xs font-medium text-gray-300">Veteran Status</label>
            <select
              value={formData.demographics.veteran_status}
              onChange={(e) =>
                setFormData((prev) => ({
                  ...prev,
                  demographics: { ...prev.demographics, veteran_status: e.target.value as any },
                }))
              }
              className="w-full bg-[#10141D] border border-white/[0.08] focus:border-emerald-500 text-white rounded-xl px-3 py-2 text-sm outline-none cursor-pointer"
            >
              <option value="Prefer not to say" className="bg-[#121820]">Prefer not to say</option>
              <option value="I am not a protected veteran" className="bg-[#121820]">Not a protected veteran</option>
              <option value="I identify as a protected veteran" className="bg-[#121820]">Protected veteran</option>
            </select>
          </div>
        </div>
      </div>

      {/* FLOATING STICKY SAVE BAR */}
      <div className="fixed bottom-0 left-0 right-0 z-40 bg-[#0B0F17]/90 backdrop-blur-md border-t border-white/[0.08] px-4 py-3.5 shadow-2xl">
        <div className="max-w-4xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-full bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center">
              {validation.isComplete ? (
                <svg className="w-4 h-4 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M5 13l4 4L19 7" />
                </svg>
              ) : (
                <span className="text-xs font-bold text-amber-400">{validation.percentage}%</span>
              )}
            </div>
            <div>
              <p className="text-white text-xs sm:text-sm font-semibold">
                {validation.isComplete ? "Preferences Complete" : `Setup Incomplete (${validation.percentage}%)`}
              </p>
              <p className="text-gray-400 text-[11px]">
                {validation.isComplete
                  ? "Ready for 1-Click Auto Apply across all target jobs"
                  : `Missing required: ${validation.missing.slice(0, 2).join(", ")}${validation.missing.length > 2 ? ` +${validation.missing.length - 2} more` : ""}`}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3 w-full sm:w-auto">
            <button
              type="button"
              onClick={handleSave}
              disabled={isSaving}
              className="flex-1 sm:flex-none bg-emerald-500 hover:bg-emerald-400 disabled:opacity-50 text-black font-semibold text-xs sm:text-sm px-6 py-2.5 rounded-xl transition-all shadow-lg cursor-pointer"
            >
              {isSaving ? "Saving..." : "Save Preferences"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

