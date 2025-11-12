import Logo from "next/image";

export default function Home() {
  return (
    <div className="w-full h-full bg-gray-50">
      <main>
        <img src="/Logo.png" alt="AurumCap Logo" />
        <section className="text-bold text-2xl">
          <h1 className="">Maneja tus inversiones desde un mismo lugar.</h1>
        </section>
      </main>
    </div>
  );
}
