import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { useCart } from '../context/CartContext';
import PaymentQR from './PaymentQR';

const ProductCard = ({ product }) => {
  const { addToCart } = useCart();
  const [showPaymentQR, setShowPaymentQR] = useState(false);

  const handleAddToCart = (e) => {
    e.preventDefault();
    e.stopPropagation();
    addToCart(product);
  };

  const handlePayNow = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setShowPaymentQR(true);
  };

  return (
    <div className="bg-white rounded-xl shadow-lg overflow-hidden hover:shadow-xl transition-shadow duration-300 group">
      <div className="relative h-48 bg-gradient-to-br from-blue-500 to-purple-600 p-6 flex items-center justify-center">
        <div className="text-center text-white">
          <div className="text-3xl mb-2">{product.icon}</div>
          <h3 className="text-xl font-bold">{product.name}</h3>
        </div>
      </div>

      <div className="p-6">
        <p className="text-gray-600 text-sm mb-4 line-clamp-3">
          {product.shortDescription}
        </p>

        <div className="flex items-center justify-between mb-4">
          <span className="text-2xl font-bold text-blue-600">
            {product.price.toLocaleString('ru-RU')} ₽
          </span>
          <span className="text-sm text-gray-500">
            {product.deliveryTime}
          </span>
        </div>

        <div className="space-y-2">
          <div className="flex space-x-2">
            <Link
              to={`/product/${product.id}`}
              className="flex-1 bg-gray-100 text-gray-700 px-4 py-2 rounded-lg hover:bg-gray-200 transition-colors text-center font-medium"
            >
              Подробнее
            </Link>
            <button
              onClick={handleAddToCart}
              className="flex-1 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors font-medium"
            >
              В корзину
            </button>
          </div>
          <button
            onClick={handlePayNow}
            className="w-full bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 transition-colors font-medium flex items-center justify-center space-x-2"
          >
            <span>💳</span>
            <span>Оплатить сейчас</span>
          </button>
        </div>
      </div>

      {/* Payment QR Modal */}
      {showPaymentQR && (
        <PaymentQR
          amount={product.price}
          onClose={() => setShowPaymentQR(false)}
        />
      )}
    </div>
  );
};

export default ProductCard;