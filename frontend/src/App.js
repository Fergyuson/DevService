import React from "react";
import "./App.css";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { CartProvider } from './context/CartContext';
import Header from './components/Header';
import HomePage from './pages/HomePage';
import CatalogPage from './pages/CatalogPage';
import CartPage from './pages/CartPage';
import ProductDetailPage from './pages/ProductDetailPage';
import PrivacyPolicyPage from "./pages/PrivacyPolicyPage";
import OfferPage from "./pages/OfferPage";

function App() {
  return (
    <CartProvider>
      <div className="App">
        <BrowserRouter>
          <Header />
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/catalog" element={<CatalogPage />} />
            <Route path="/cart" element={<CartPage />} />
            <Route path="/product/:id" element={<ProductDetailPage />} />
            <Route path="/services" element={<CatalogPage />} />
            <Route path="/policy" element={<PrivacyPolicyPage />} />
            <Route path="/offer" element={<OfferPage />} />
          </Routes>
        </BrowserRouter>
      </div>
    </CartProvider>
  );
}

export default App;