import axios from 'axios';

// В Docker контейнере фронтенд и бэкенд на одном домене
// Поэтому используем относительные пути
const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || '';
const API = `${BACKEND_URL}/api`;

console.log('Backend URL:', BACKEND_URL);
console.log('API URL:', API);

// Products API
export const getProducts = async () => {
  try {
    const response = await axios.get(`${API}/products`);
    return response.data;
  } catch (error) {
    console.error('Error fetching products:', error);
    throw error;
  }
};

export const getProduct = async (productId) => {
  try {
    const response = await axios.get(`${API}/products/${productId}`);
    return response.data;
  } catch (error) {
    console.error('Error fetching product:', error);
    throw error;
  }
};

// Cart API
export const saveCart = async (cartData) => {
  try {
    const response = await axios.post(`${API}/cart/save`, cartData);
    return response.data;
  } catch (error) {
    console.error('Error saving cart:', error);
    throw error;
  }
};

export const getCart = async (sessionId) => {
  try {
    const response = await axios.get(`${API}/cart/${sessionId}`);
    return response.data;
  } catch (error) {
    console.error('Error fetching cart:', error);
    throw error;
  }
};

export const getBanks = async () => {
  try {
    const response = await axios.get(`${API}/banks`);
    return response.data.banks; // Возвращаем только banks из ответа
  } catch (error) {
    console.error('Error fetching banks:', error);
    throw error;
  }
};


// QR Code API
export const getQRCode = async (bank, amount) => {
  try {
    const response = await axios.get(`${API}/qr-code/${bank}/${amount}`);
    return response.data;
  } catch (error) {
    console.error('Error fetching QR code:', error);
    throw error;
  }
};