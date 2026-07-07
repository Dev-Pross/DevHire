import React from 'react';

interface UpgradePopupProps {
  isOpen: boolean;
  onClose: () => void;
  message: string;
}

export const UpgradePopup: React.FC<UpgradePopupProps> = ({ isOpen, onClose, message }) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
      <div className="bg-[#1A1A1A] border border-white/[0.08] rounded-2xl p-6 sm:p-8 max-w-md w-full shadow-2xl relative">
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-gray-500 hover:text-white transition-colors"
        >
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
        
        <div className="flex flex-col items-center text-center">
          <div className="w-12 h-12 bg-emerald-500/10 rounded-full flex items-center justify-center mb-4 border border-emerald-500/20">
            <svg className="w-6 h-6 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
          </div>
          
          <h3 className="text-xl font-bold text-white mb-2">Upgrade to Pro</h3>
          
          <p className="text-gray-400 mb-6 text-sm">
            {message}
          </p>
          
          <a
            href="mailto:tejabudumuru3@gmail.com"
            className="w-full bg-emerald-500 text-black py-3 px-6 rounded-xl font-semibold hover:bg-emerald-400 transition-colors text-center block"
          >
            Upgrade to Pro
          </a>
        </div>
      </div>
    </div>
  );
};
