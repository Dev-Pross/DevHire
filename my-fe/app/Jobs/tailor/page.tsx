'use client';
import Navbar from '../../Components/Navbar';
import dynamic from 'next/dynamic';

const TailorResumeV2 = dynamic(
  () => import('../../Components/tailor-v2/TailorResumeV2').then((mod) => mod.TailorResumeV2),
  { ssr: false }
);

export default function Page() {
  return (
    <div className="h-screen flex flex-col bg-[#0A0A0A] overflow-hidden">
      <div className="shrink-0">
        <Navbar />
      </div>
      <main className="flex-1 min-h-0 w-full">
        <TailorResumeV2 />
      </main>
    </div>
  );
}
