import React, { useRef } from 'react';
import { Link } from 'react-router-dom';

const HomePage = () => {
  const footerRef = useRef(null);

  const scrollToFooter = () => {
    footerRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  return (
      <div className="pt-16 min-h-screen bg-gray-50">

        <section className="bg-gradient-to-r from-blue-600 to-purple-700 text-white py-20">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
              <div>
                <h1 className="text-4xl lg:text-6xl font-bold mb-6">
                  Профессиональная разработка
                </h1>
                <p className="text-xl mb-8 text-blue-100">
                  Создаем веб-сайты, мобильные приложения и цифровые решения для вашего бизнеса
                </p>
                <div className="flex flex-col sm:flex-row gap-4 sm:justify-center sm:items-center mx-auto">
                  <Link
                      to="/catalog"
                      className="bg-white text-blue-600 px-8 py-3 rounded-lg font-semibold hover:bg-gray-100 transition-colors text-center"
                  >
                    Посмотреть услуги
                  </Link>
                  <button
                      onClick={scrollToFooter}
                      className="border-2 border-white text-white px-8 py-3 rounded-lg font-semibold hover:bg-white hover:text-blue-600 transition-colors"
                  >
                    Связаться с нами
                  </button>
                </div>

                {/* Подпись с ссылкой на политику */}
                <div className="mt-6">
                  <Link
                      to="/policy"
                      className="text-sm text-blue-100 underline hover:text-white"
                      aria-label="Политика обработки персональных данных"
                  >
                    Политика обработки персональных данных
                  </Link>
                </div>
              </div>

              <div className="hidden lg:block">
                <img
                    src="https://images.unsplash.com/photo-1579403124614-197f69d8187b?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NDQ2NDJ8MHwxfHNlYXJjaHwxfHxzb2Z0d2FyZSUyMGRldmVsb3BtZW50fGVufDB8fHx8MTc1MzI3Nzc4M3ww&ixlib=rb-4.1.0&q=85"
                    alt="Software Development"
                    className="rounded-lg shadow-xl"
                />
              </div>
            </div>
          </div>
        </section>

        <section className="bg-white py-16">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="text-center mb-12">
              <h2 className="text-3xl font-bold text-gray-900 mb-4">
                Почему выбирают нас
              </h2>
              <p className="text-xl text-gray-600">
                Мы предоставляем высококачественные услуги разработки
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
              <div className="text-center">
                <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <span className="text-2xl">⚡</span>
                </div>
                <h3 className="text-xl font-semibold mb-2">Быстрая разработка</h3>
                <p className="text-gray-600">Соблюдаем сроки и быстро реализуем проекты</p>
              </div>

              <div className="text-center">
                <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <span className="text-2xl">🎯</span>
                </div>
                <h3 className="text-xl font-semibold mb-2">Качественный код</h3>
                <p className="text-gray-600">Используем современные технологии и лучшие практики</p>
              </div>

              <div className="text-center">
                <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <span className="text-2xl">💬</span>
                </div>
                <h3 className="text-xl font-semibold mb-2">Поддержка 24/7</h3>
                <p className="text-gray-600">Всегда готовы помочь и ответить на вопросы</p>
              </div>
            </div>
          </div>
        </section>

        <footer
            ref={footerRef}
            id="contact"
            className="bg-gray-900 text-gray-200 py-12 mt-auto"
        >
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 grid grid-cols-1 md:grid-cols-2 gap-8">
            <div>
              <h3 className="text-xl font-semibold mb-4">О нас</h3>
              <p>ИП Сергеев Артем Игоревич</p>
              <p>ИНН 463249348400</p>
              <p>ОГРНИП 325460000026418</p>
              <p>г. Курск, ул. Студенческая, д. 8, кв. 29</p>
            </div>
            <div>
              <h3 className="text-xl font-semibold mb-4">Связаться с нами</h3>
              <p>
                E-mail:{" "}
                <a
                    href="mailto:famlink.power.kursk@mail.ru"
                    className="text-blue-400 hover:underline"
                >
                  famlink.power.kursk@mail.ru
                </a>
              </p>
            </div>
          </div>
        </footer>
      </div>
  );
};

export default HomePage;
