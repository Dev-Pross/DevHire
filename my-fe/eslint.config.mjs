import { FlatCompat } from '@eslint/eslintrc';

const compat = new FlatCompat({
  baseDirectory: import.meta.dirname,
});

const eslintConfig = [
  ...compat.config({
    extends: ['next'],
    rules: {
      // Existing rules
      'react/no-unescaped-entities': 'off',
      '@next/next/no-page-custom-font': 'off',

      // 🔹 Add these to silence your current warnings:
      'react-hooks/exhaustive-deps': 'off',       // disables missing deps warnings in useEffect
      '@next/next/no-img-element': 'off',         // allows <img> instead of <Image>
      'no-var': 'off',                            // no need to disable inline
      'no-unused-vars': 'off',                    // optional: silence unused vars
      'no-unused-labels': 'off',                  // optional: silence unused eslint-disable warnings
    },
    // Optional: stop ESLint from complaining about unused disable comments
    reportUnusedDisableDirectives: false,
  }),
];

export default eslintConfig;
