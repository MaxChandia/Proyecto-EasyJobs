import React from "react";
import { BrowserRouter, Route, Routes } from "react-router-dom";
import ScrollToTop from "./component/scrollToTop";
import { Home } from "./pages/home";
import { Login } from "./pages/login";
import { Perfil } from "./pages/perfil";
import { SegundoPerfil } from "./pages/PerfilPublicaciones.js";
import injectContext from "./store/appContext";
import { Navbar } from "./component/navbar";
import { OtroFormulario } from "./pages/Formulario.jsx";
import { Nosotros } from "./component/nosotros.js";
import PrestadorCv from "./pages/prestadorCv.js";
import GeneradorPublicacion from "./pages/generadorPublicacion.js";

//create your first component
const Layout = () => {
  //the basename is used when your project is published in a subdirectory and not in the root of the domain
  // you can set the basename on the .env file located at the root of this project, E.g:: BASENAME=/react-hello-webapp/
  const basename = process.env.BASENAME || "";

  if (!process.env.BACKEND_URL || process.env.BACKEND_URL == "")
    return <BackendURL />;

  return (
    <div>
      <BrowserRouter basename={basename}>
        <ScrollToTop>
          <Navbar />
          <Routes>
            <Route element={<Home />} path="/" />
            <Route element={<Login />} path="/login" />
            <Route element={<PrestadorCv />} path="/Trabajos" />
            <Route element={<OtroFormulario />} path="/Registro" />
            <Route element={<GeneradorPublicacion />}path="/generadorPublicacion"/>
            <Route element={<Perfil />} path="/perfil" />
            <Route element={<SegundoPerfil />} path="/Prestador/"/>
            <Route element={<SegundoPerfil />} path="/Prestador/:idUsuario" />
            <Route element={<Nosotros />} path="/nosotros" />
            <Route element={<h1>Not found!</h1>} />
          </Routes>
        </ScrollToTop>
      </BrowserRouter>
    </div>
  );
};

export default injectContext(Layout);