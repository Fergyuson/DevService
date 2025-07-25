import React, { useState, useEffect, useCallback } from 'react';
import { getBanks, getQRCode } from '../services/api';

const PaymentQR = ({ amount, onClose }) => {
  const [banks, setBanks] = useState({});
  const [selectedBank, setSelectedBank] = useState('');
  const [qrData, setQrData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // Загрузка списка банков
  useEffect(() => {
    const fetchBanks = async () => {
      try {
        const banksData = await getBanks();
        setBanks(banksData || {});
        const firstBank = Object.keys(banksData || {})[0];
        if (firstBank) setSelectedBank(firstBank);
      } catch (err) {
        console.error('Error fetching banks:', err);
        setError('Ошибка загрузки банков');
        const fallback = { sovcombank: { name: 'Совкомбанк', icon: '🏦' } };
        setBanks(fallback);
        setSelectedBank('sovcombank');
      }
    };

    fetchBanks();
  }, []);

  // Генерация QR — мемоизированный колбэк, чтобы корректно выставить зависимости
  const fetchQRCode = useCallback(
      async (payAmount) => {
        if (!selectedBank) {
          setError('Выберите банк');
          return;
        }

        setLoading(true);
        setError('');
        setQrData(null);

        try {
          const data = await getQRCode(selectedBank, payAmount);
          setQrData(data);
        } catch (err) {
          console.error('Error fetching QR code:', err);
          if (err.response?.status === 404) {
            setError(
                `QR-код для банка "${banks[selectedBank]?.name}" на сумму ${payAmount}₽ не найден`
            );
          } else {
            setError('Ошибка загрузки QR-кода');
          }
        } finally {
          setLoading(false);
        }
      },
      [banks, selectedBank]
  );

  // Автовызов генерации при выборе банка или изменении фиксированной суммы
  useEffect(() => {
    if (selectedBank && amount) {
      fetchQRCode(amount);
    }
  }, [selectedBank, amount, fetchQRCode]);

  const handleBankChange = (bank) => {
    setSelectedBank(bank);
    setQrData(null);
  };

  const generateQRImageUrl = (qrUrl) =>
      `https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=${encodeURIComponent(qrUrl)}`;

  return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
        <div className="bg-white rounded-2xl max-w-md w-full max-h-[90vh] overflow-y-auto">
          <div className="p-6">
            {/* Header */}
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-2xl font-bold text-gray-900">Оплата QR-кодом</h2>
              <button
                  onClick={onClose}
                  className="text-gray-400 hover:text-gray-600 text-2xl font-bold"
                  aria-label="Закрыть"
                  type="button"
              >
                ×
              </button>
            </div>

            {/* Fixed Amount */}
            <div className="text-center mb-4">
              <div className="text-lg text-gray-600">
                К оплате:&nbsp;
                <span className="font-semibold">
                {amount.toLocaleString('ru-RU')} ₽
              </span>
              </div>
            </div>

            {/* Bank Selection */}
            <div className="mb-6">
              <h3 className="text-lg font-semibold mb-3">Выберите банк:</h3>
              <div className="grid grid-cols-2 gap-3">
                {Object.entries(banks).map(([bankKey, bankData]) => (
                    <button
                        key={bankKey}
                        onClick={() => handleBankChange(bankKey)}
                        className={`p-3 rounded-lg border-2 transition-colors ${
                            selectedBank === bankKey
                                ? 'border-blue-500 bg-blue-50'
                                : 'border-gray-200 hover:border-gray-300'
                        }`}
                        type="button"
                    >
                      <div className="text-2xl mb-1">{bankData.icon}</div>
                      <div className="text-sm font-medium">{bankData.name}</div>
                    </button>
                ))}
              </div>
              {Object.keys(banks).length === 0 && (
                  <div className="text-gray-500 text-center py-4">
                    Загрузка банков...
                  </div>
              )}
            </div>

            {/* QR Code */}
            <div className="text-center">
              {loading ? (
                  <div className="py-8">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
                    <p className="text-gray-600">Загрузка QR-кода...</p>
                  </div>
              ) : error ? (
                  <div className="py-8">
                    <div className="text-red-500 text-4xl mb-4">⚠️</div>
                    <p className="text-red-600 mb-4">{error}</p>
                    <button
                        onClick={() => fetchQRCode(amount)}
                        className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
                        type="button"
                    >
                      Попробовать снова
                    </button>
                  </div>
              ) : qrData?.qr_url ? (
                  <div className="space-y-4">
                    <div className="bg-white p-4 rounded-lg border-2 border-gray-200">
                      <img
                          src={generateQRImageUrl(qrData.qr_url)}
                          alt="QR Code для оплаты"
                          className="mx-auto w-48 h-48"
                          onError={(e) => {
                            e.currentTarget.style.display = 'none';
                            setError('Ошибка загрузки QR-кода');
                          }}
                      />
                    </div>
                    <div className="space-y-2">
                      <div className="text-lg font-bold text-green-600">
                        К оплате: {amount.toLocaleString('ru-RU')} ₽
                      </div>
                      <p className="text-sm text-gray-600">
                        Отсканируйте QR-код в приложении {banks[selectedBank]?.name}
                      </p>
                      <div className="space-y-2">
                        <a
                            href={qrData.qr_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="inline-block bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition-colors"
                        >
                          Открыть в приложении
                        </a>
                        <div className="text-xs text-gray-500">
                          Банк: {qrData.bank} | Сумма: {qrData.amount}₽
                        </div>
                      </div>
                    </div>
                  </div>
              ) : selectedBank ? (
                  <div className="py-8">
                    <button
                        onClick={() => fetchQRCode(amount)}
                        className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 transition-colors"
                        type="button"
                    >
                      Сгенерировать QR-код
                    </button>
                  </div>
              ) : (
                  <div className="py-8">
                    <p className="text-gray-600">Выберите банк для генерации QR-кода</p>
                  </div>
              )}
            </div>

            {/* Instructions */}
            <div className="mt-6 p-4 bg-gray-50 rounded-lg">
              <h4 className="font-semibold mb-2">Инструкция по оплате:</h4>
              <ol className="text-sm text-gray-600 space-y-1">
                <li>1. Откройте приложение {banks[selectedBank]?.name || 'банка'}.</li>
                <li>2. Найдите функцию «Оплата по QR».</li>
                <li>3. Отсканируйте QR-код.</li>
                <li>4. Подтвердите платеж на сумму {amount.toLocaleString('ru-RU')} ₽.</li>
              </ol>
            </div>

            {/* Close */}
            <div className="mt-6">
              <button
                  onClick={onClose}
                  className="w-full bg-gray-100 text-gray-700 py-3 rounded-lg hover:bg-gray-200 transition-colors"
                  type="button"
              >
                Закрыть
              </button>
            </div>
          </div>
        </div>
      </div>
  );
};

export default PaymentQR;
