'use client';
import Navbar from '../../Components/Navbar';
import dynamic from 'next/dynamic';

const Tailor_resume = dynamic(
  () => import('../../Components/Tailor_resume'),
  { ssr: false }
);

export default function Page() {
  return (
    <div className="page-section">
      <Navbar />
      <Tailor_resume />
    </div>
  );
}
