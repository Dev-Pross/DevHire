export const HeroTalent = () => {
  return (

    <section className="h-screen w-full flex items-center px-30  ">
      <div className="flex-1 max-w-xl">
        <h1 className="text-6xl font-bold text-white  leading-tight mb-6">
          Build Amazing Products withsome amazing Developers   <br />
         
        </h1>
        
        <p className="text-xl text-stone-200 mb-8 leading-relaxed">
          Transform your ideas into reality with our cutting-edge solutions.
        </p>
        <div className="space-x-4">
          <button className="bg-blue-600 hover:bg-blue-700 text-white px-8 py-4 rounded-lg transition-colors">
            Get Started
          </button>
          <button className="border border-gray-300 text-gray-700 px-8 py-4 rounded-lg hover:bg-gray-50 transition-colors">
            Learn More
          </button>
        </div>
      </div>

      <div className="flex-1 flex justify-end opacity-80">
        <div className="relative">
          <img
            src="/ne.jpg"
            alt="Product showcase"
            className="w-96 h-150 object-cover rounded-2xl shadow-2xl "
          />
            <div className="absolute -top-4 -right-4 w-24 h-24 bg-blue-500 rounded-full opacity-20"></div>
        </div>
      </div>
    </section>
  );
};
