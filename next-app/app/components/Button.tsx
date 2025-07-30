import React from "react";

interface ButtonProps {
  children: React.ReactNode;
  onClick: () => void;
  variant?: "primary" | "secondary";
  size?: "sm" | "md" | "lg";
  disabled: boolean;

}

const Button = ({
  children,
  onClick,
  variant = "primary",
  size = "md",
  disabled = false,
}: ButtonProps) => {
  const getClass = () => {
    const baseClassname =
      "px-4 py-2 border-none rounded-md cursor-pointer text-sm font-medium transition-colors";
    const variantClass: Record<string, string> = {
      primary: "bg-blue-600 text-white hover:bg-black hover:text-white",
      secondary: "bg-gray-200 text-gray-800 hover:bg-gray-300",
    };
    const sizeClass: Record<string, string> = {
      sm: "px-3 py-1.5 text-sm", // Small
      md: "px-4 py-2 text-sm", // Medium (default)
      lg: "px-6 py-3 text-base", // Large
    };
    const vClass = variantClass[variant] || variantClass.primary;
    const sClass = sizeClass[size] || sizeClass.md;
    if (disabled) {
      return `${baseClassname}  ${sizeClass} bg-gray-300 text-gray-500 cursor-not-allowed`;
    }
    return `${baseClassname} ${vClass} ${sClass}`;
  };

  return (
    <div className="flex items-center justify-center w-full">
      <button
        onClick={disabled ? undefined : onClick} // Prevent onClick when disabled
        disabled={disabled}
        className={getClass()}
      >
        {children}
      </button>
    </div>
  );
};

export default Button;
