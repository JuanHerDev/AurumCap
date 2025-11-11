import Logo from "next/image";

export default function Home() {
  return (
    <div className="w-full h-full bg-gray-50">
      <main className="text-2xl">
        <img 
          src="/Logo.png" 
          alt="AurumCap Logo" 
          className="w-36 h-36"
        />
        <h1 className="text-yellow-700 font-semibold">
          Bienvenidos a AurumCap
        </h1>
      </main>
    </div>
  );
}
