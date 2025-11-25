import Link from "next/link";
import Image from "next/image";

export default function Home() {
  return (
    <div className="min-h-screen bg-black text-white">
      <div className="min-h-screen flex flex-col items-center justify-center px-6 py-8 md:py-12">
        
        {/* Logo Section */}
        <div className="flex flex-col items-center gap-4 md:gap-6 mb-8 md:mb-12">
          <Image 
            src="/Logo.png"
            alt="AurumCap Logo"
            width={50}
            height={150}
            className="w-20 h-20 md:w-32 md:h-32 lg:w-40 lg:h-40"
          />
          
          {/* Text: AurumCap */}
          <h2 className="text-[#CCB661] text-3xl md:text-5xl lg:text-6xl font-bold drop-shadow-md">
            AurumCap
          </h2>
        </div>
      <br/>
        {/* Main Text */}
        <section className="text-center mb-8 md:mb-12 lg:mb-16 max-w-2xl">
          <h1 className="font-bold text-2xl md:text-4xl lg:text-5xl mb-4 md:mb-6 lg:mb-8 leading-tight">
            Invierte sin complicarte
          </h1>
          <p className="text-gray-300 text-sm md:text-lg lg:text-xl leading-relaxed">
            Maneja tus inversiones desde un mismo lugar de forma<br className="hidden md:block" />
            inteligente y segura.
          </p>
        </section>
<br/>
 {/* Action Buttons */}
        <section className="w-full max-w-xs md:max-w-md space-y-3 md:space-y-0 md:flex md:justify-center md:gap-4 lg:gap-6 mb-8 md:mb-12 lg:mb-16">
  
  {/* CREAR CUENTA */}
  <Link
    href="/register"
    className="
      w-full md:w-auto flex items-center justify-center 
       w-full md:w-auto flex items-center justify-center 
      border-2 border-[#B59F50] text-[#B59F50] 
      font-bold text-lg md:text-xl

      py-3 md:py-4 lg:py-5
      px-8 md:px-12 lg:px-16

      hover:!py-2 hover:!px-8  /* 👈 IGUAL CRECE EL CUADRO */
      hover:bg-[#B59F50] hover:text-black

      rounded-xl
      transition-all duration-300
      hover:scale-105
    "
  >
    Crear cuenta
  </Link>

  {/* INICIAR SESIÓN */}
  <Link
    href="/login"
    className="
      w-full md:w-auto flex items-center justify-center 
      border-2 border-[#B59F50] text-[#B59F50] 
      font-bold text-lg md:text-xl

      py-3 md:py-4 lg:py-5
      px-8 md:px-12 lg:px-16

      hover:!py-2 hover:!px-8  /* 👈 IGUAL CRECE EL CUADRO */
      hover:bg-[#B59F50] hover:text-black

      rounded-xl
      transition-all duration-300
      hover:scale-105
    "
  >
    Iniciar sesión
  </Link>

</section>

      <br/>
        {/* Benefits */}
        <section className="w-full max-w-xs md:max-w-4xl mb-8 md:mb-12 lg:mb-16">
          <h3 className="text-[#CCB661] font-semibold text-lg md:text-2xl lg:text-3xl mb-4 md:mb-8 lg:mb-12 text-center">
            Nuestros Beneficios
          </h3>
          <br/>
          {/* Mobile: Lista vertical */}
          <div className="block md:hidden space-y-3">
            {[
              { icon: "📚", text: "Aprende" },
              { icon: "💼", text: "Invierte" },
              { icon: "📈", text: "Crecimiento" }
            ].map((benefit, index) => (
              <div key={index} className="flex items-center gap-3 bg-gray-900/50 rounded-lg p-3">
                <span className="text-lg">{benefit.icon}</span>
                <span className="font-medium">{benefit.text}</span>
              </div>
            ))}
          </div>

          
          {/* Desktop: Grid de 3 columnas */}
<div className="hidden md:grid grid-cols-1 sm:grid-cols-3 gap-4 md:gap-6 lg:gap-8">
  {[
    { 
      icon: "🎓", 
      text: "Aprende", 
      desc: "Educación financiera accesible" 
    },
    { 
      icon: "💼", 
      text: "Invierte", 
      desc: "Plataforma intuitiva de inversión" 
    },
    { 
      icon: "📈", 
      text: "Crecimiento", 
      desc: "Sigue tu progreso en tiempo real" 
    }
  ].map((benefit, index) => (
    <div 
      key={index} 
      className="
        group flex flex-col items-center
        p-6 rounded-xl 
        transition-all duration-300
        bg-transparent
        hover:bg-gray-900/50 
        hover:scale-105
      "
    >
      {/* ICONO con CUADRADO DORADO QUE DESAPARECE EN HOVER */}
      <span
        className="
          bg-[#B59F50] 
          rounded-xl 
          flex items-center justify-center 
          transition-all duration-300
          size-12
          shadow-lg

          group-hover:bg-transparent  /* Desaparece */
          group-hover:shadow-none
        "
      >
        <span className="text-3xl transition-all duration-300 group-hover:text-4xl">
          {benefit.icon}
        </span>
      </span>

      {/* TEXTO OCULTO HASTA HOVER */}
      <div 
        className="
          text-center mt-4 opacity-0 
          group-hover:opacity-100 
          group-hover:mt-6
          transition-all duration-300
        "
      >
        <div className="font-semibold text-lg md:text-xl mb-1">
          {benefit.text}
        </div>
        <div className="text-gray-400 text-sm">
          {benefit.desc}
        </div>
      </div>
    </div>
  ))}
</div>

        </section>

        {/* Footer links */}
        <footer className="flex gap-4 md:gap-6 lg:gap-8 text-sm md:text-base text-gray-400 mt-auto pt-8">
          <Link
            href="/privacy"
            className="hover:text-[#CCB661] transition-colors duration-200"
          >
            Política de Privacidad
          </Link>

          <Link
            href="/support"
            className="hover:text-[#CCB661] transition-colors duration-200"
          >
            Soporte
          </Link>
        </footer>
      </div>
    </div>
  );
}