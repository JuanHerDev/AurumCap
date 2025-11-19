import Logo from "next/image";

export default function Home() {
  return (
    <div className="w-full h-screen bg-black flex flex-col items-center justify-center gap-6">
      
      {/* Logo */}
      <img
        src="/Logo.png"
        alt="AurumCap Logo"
        className="w-40 h-auto"
      />

      {/* Texto AurumCap en dorado */}
      <h2 className="text-[#CCB661] text-3xl font-bold drop-shadow-md">
        AurumCap
      </h2>

      {/* Texto principal */}
      <section>
        <h1 className="text-white font-bold text-2xl text-center max-w-xs">
          Maneja tus inversiones desde un mismo lugar.
        </h1>
      </section>

      {/* Botón Iniciar sesión */}
      <a
        href="/login"
        className="w-36 h-10 flex items-center justify-center bg-[#B59F50] !text-black font-bold text-lg rounded-xl shadow-lg hover:bg-[#A68F45] transition"
      >
        Iniciar sesión
      </a>
    </div>
  );
}


