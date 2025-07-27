// src/PolicyPage.js
import React, { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";

const PolicyPage = () => {
    const SAFE_GAP = 24; // доп. зазор от фиксированного хедера
    const [headerHeight, setHeaderHeight] = useState(0);

    useEffect(() => {
        const header = document.querySelector("header");
        const measure = () => {
            const h = header?.getBoundingClientRect().height ?? 0;
            setHeaderHeight(Math.ceil(h));
        };
        measure();
        window.addEventListener("resize", measure);

        let ro;
        if (header && "ResizeObserver" in window) {
            ro = new ResizeObserver(measure);
            ro.observe(header);
        }
        return () => {
            window.removeEventListener("resize", measure);
            if (ro) ro.disconnect();
        };
    }, []);

    const paddingTop = useMemo(() => {
        const minPt = 112; // минимум, если хедер не найден
        return Math.max(minPt, headerHeight + SAFE_GAP);
    }, [headerHeight]);

    return (
        <main
            className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 pb-16 text-gray-800 text-left"
            style={{ paddingTop, textAlign: "left" }} // жёстко прижимаем влево на случай глобальных стилей
        >
            {/* Единственный центрированный заголовок */}
            <h1 className="text-3xl md:text-4xl font-bold text-center mb-10">
                Политика обработки персональных данных
            </h1>

            {/* 1. Термины и определения */}
            <section aria-labelledby="sec-1">
                <h2 id="sec-1" className="text-2xl md:text-3xl font-bold mt-8 mb-6 text-left">
                    1. Термины и определения
                </h2>

                <p className="mb-3">
                    <span className="font-semibold">1.1 Компания</span> — ИП Сергеев Артём Игоревич (ИНН
                    463249348400, ОГРНИП 325460000026418), самостоятельно или совместно с другими лицами
                    организующий и (или) осуществляющий Обработку персональных данных, а также определяющий
                    цели Обработки персональных данных, состав Персональных данных, подлежащих Обработке,
                    действия (операции), совершаемые с Персональными данными Пользователей Сайта.
                </p>

                <p className="mb-3">
                    <span className="font-semibold">1.2. Сайт</span> — информационный ресурс в сети
                    «Интернет», администрируемый Компанией, расположенный по адресу{" "}
                    <a
                        href="https://e-devservice.ru/"
                        target="_blank"
                        rel="noreferrer"
                        className="text-blue-700 underline"
                    >
                        https://e-devservice.ru/
                    </a>
                    .
                </p>

                <p className="mb-3">
                    <span className="font-semibold">1.3. Пользователь</span> — совершеннолетнее физическое
                    лицо, намеренное использовать или использующее Сайт.
                </p>

                <p className="mb-3">
                    <span className="font-semibold">1.4. Персональные данные</span> — информация, которая
                    позволяет прямо или косвенно идентифицировать Пользователя.
                </p>

                <p className="mb-3">
                    <span className="font-semibold">1.5. Обработка персональных данных</span> — любое действие
                    (операция) или совокупность действий (операций), совершаемых с использованием средств
                    автоматизации или без использования таких средств с персональными данными, включая сбор,
                    запись, систематизацию, накопление, хранение, уточнение (обновление, изменение),
                    извлечение, использование, передачу (предоставление, доступ), обезличивание, блокирование,
                    удаление, уничтожение персональных данных.
                </p>

                <p className="mb-3">
                    <span className="font-semibold">1.6. Форма</span> — поле Сайта, доступное для заполнения
                    Пользователем, в которое Пользователем вносятся Персональные данные.
                </p>

                <p className="mb-3">
                    <span className="font-semibold">1.7. Рекламные сообщения</span> — уведомления и сообщения
                    о новых продуктах и услугах Компании, специальных предложениях, предлагаемых к посещению
                    мероприятий и событий, проводимых Компанией.
                </p>
            </section>

            {/* 2. Общие положения */}
            <section aria-labelledby="sec-2">
                <h2 id="sec-2" className="text-2xl md:text-3xl font-bold mt-10 mb-6 text-left">
                    2. Общие положения
                </h2>

                <p className="mb-3">
                    <span className="font-semibold">2.1</span> Настоящая политика конфиденциальности (далее —
                    «Политика») составлена в соответствии с требованиями Федерального закона от 27.07.2006 г.
                    №152-ФЗ «О персональных данных» и определяет порядок Обработки персональных данных и меры
                    по обеспечению безопасности Персональных данных Пользователей.
                </p>

                <p className="mb-3">
                    <span className="font-semibold">2.2</span> Фактическое использование Пользователем Сайта
                    означает безоговорочное согласие с Политикой и указанными в ней условиями обработки его
                    Персональных данных.
                </p>

                <p className="mb-3">
                    <span className="font-semibold">2.3</span> В случае несогласия с этими условиями
                    Пользователь должен воздержаться от использования Сайта.
                </p>

                <p className="mb-2">
                    <span className="font-semibold">2.4 Пользователь вправе:</span>
                </p>
                <ul className="list-disc pl-6 space-y-2 mb-4">
                    <li>
                        получать информацию, касающуюся обработки его Персональных данных, за исключением
                        случаев, предусмотренных действующим законодательством РФ;
                    </li>
                    <li>
                        требовать от Компании уточнения его Персональных данных и (или) их блокирования и (или)
                        уничтожения в случае, если Персональные данные являются неполными, устаревшими,
                        неточными, незаконно полученными и (или) не являются необходимыми для заявленной цели
                        обработки;
                    </li>
                    <li>принимать предусмотренные действующим законодательством РФ меры по защите своих прав;</li>
                    <li>
                        реализовывать иные права, предусмотренные Федеральным законом от 27.07.2006 г. №152-ФЗ
                        «О персональных данных».
                    </li>
                </ul>
            </section>

            {/* 3. Цели и объём */}
            <section aria-labelledby="sec-3">
                <h2 id="sec-3" className="text-2xl md:text-3xl font-bold mt-10 mb-6 text-left">
                    3. Цели Обработки и объем обрабатываемых персональных данных
                </h2>

                <p className="mb-2">
          <span className="font-semibold">3.1 Общие цели Обработки персональных данных
          Пользователя:</span>
                </p>
                <ul className="list-disc pl-6 space-y-2 mb-4">
                    <li>
                        обеспечение соблюдения Конституции РФ, федеральных законов и иных нормативных правовых
                        актов РФ;
                    </li>
                    <li>обеспечение качественной работы Сайта;</li>
                    <li>внесение изменений в Сайт для улучшения его работы;</li>
                    <li>направление Пользователю Рекламных сообщений;</li>
                    <li>предоставление поддержки при использовании Сайта в случае возникновения трудностей.</li>
                </ul>

                <p className="mb-2">
          <span className="font-semibold">3.2 Перечень обрабатываемых Персональных данных
          Пользователя:</span>
                </p>

                <p className="mb-3">
                    <span className="font-semibold">3.2.1 Когда Пользователь связывается с Компанией.</span>{" "}
                    Мы собираем данные, которые Пользователь сообщает нам при заполнении контактной формы на
                    Сайте или сообщает в устной (например, во время звонка по Zoom) или письменной форме
                    (например, в электронном письме). Обрабатываются: полное имя, адрес электронной почты,
                    номер телефона и иная информация, которую Пользователь предоставляет.
                </p>

                <p className="mb-3">
          <span className="font-semibold">
            3.2.2 Когда Пользователь подает заявку на вступление в команду Компании.
          </span>{" "}
                    Собирается информация из резюме и дополнительные сведения, предоставленные в устной или
                    письменной форме.
                </p>

                <p className="mb-3">
          <span className="font-semibold">
            3.2.3 Данные, которые автоматически собираются при посещении Сайта и поддоменов.
          </span>
                </p>

                <p className="mb-3">
                    <span className="font-semibold">3.2.4 Услуги третьих лиц.</span> Используется Google
                    Analytics для сбора стандартной информации и анализа поведения посетителей. Информация
                    обрабатывается анонимно.
                </p>

                <p className="mb-3">
                    <span className="font-semibold">3.2.5 Cookie‑файлы.</span> Применяются для персонализации
                    сервиса и улучшения работы сайта.
                </p>
            </section>

            {/* 4. Условия обработки */}
            <section aria-labelledby="sec-4">
                <h2 id="sec-4" className="text-2xl md:text-3xl font-bold mt-10 mb-6 text-left">
                    4. Условия Обработки персональных данных
                </h2>

                <h3 className="text-xl md:text-2xl font-bold mt-6 mb-4 text-left">
                    Правовые основания Обработки персональных данных
                </h3>
                <p className="mb-3">
                    <span className="font-semibold">4.1</span> Основания: ст. 24 Конституции РФ; Гражданский
                    кодекс РФ; Федеральный закон № 129-ФЗ от 08.08.2001; иные НПА; документы о госрегистрации
                    Оператора; согласие Пользователя.
                </p>
                <p className="mb-6">
                    <span className="font-semibold">4.2</span> Обработка ведётся по требованиям Федерального
                    закона №152‑ФЗ «О персональных данных».
                </p>

                <h3 className="text-xl md:text-2xl font-bold mt-6 mb-4 text-left">
                    Порядок Обработки персональных данных
                </h3>

                <p className="mb-3">
                    <span className="font-semibold">4.3 Для связи с Пользователем.</span> Контакты,
                    предоставленные Пользователем, используются для коммуникации и предоставления запрошенной
                    информации.
                </p>

                <p className="mb-3">
                    <span className="font-semibold">4.4 Для установления деловых отношений.</span> Контактная
                    информация используется для заключения и исполнения договорных отношений и информирования
                    об услугах.
                </p>

                <p className="mb-6">
                    <span className="font-semibold">4.5 Для предоставления информации.</span> E‑mail может
                    применяться для отправки обновлений, новостей и кейсов.
                </p>

                <h3 className="text-xl md:text-2xl font-bold mt-6 mb-4 text-left">
                    Сроки Обработки персональных данных
                </h3>
                <p className="mb-6">
                    <span className="font-semibold">4.6</span> Обработка ведётся в течение неопределённого
                    срока.
                </p>

                <h3 className="text-xl md:text-2xl font-bold mt-6 mb-4 text-left">
                    Передача и раскрытие третьим лицам
                </h3>
                <p className="mb-3">
                    <span className="font-semibold">4.7</span> Передача допускается: при согласии
                    Пользователя; для исполнения договора; для соблюдения закона; при продаже Сайта с
                    переходом обязательств к приобретателю.
                </p>
                <p className="mb-6">
                    <span className="font-semibold">4.8</span> Раскрытие ПД возможно по требованию суда,
                    правоохранительных органов и в иных случаях, предусмотренных законодательством РФ.
                </p>

                <h3 className="text-xl md:text-2xl font-bold mt-6 mb-4 text-left">
                    Прекращение обработки
                </h3>
                <p className="mb-3">
                    <span className="font-semibold">4.9</span> Прекращение — при достижении целей; при отзыве
                    согласия; при прекращении деятельности Оператора; при выявлении неправомерной обработки.
                </p>

                <h3 className="text-xl md:text-2xl font-bold mt-6 mb-4 text-left">
                    Хранение Персональных данных
                </h3>
                <p className="mb-6">
                    <span className="font-semibold">4.10</span> Применяются необходимые технические и
                    административные меры. Данные хранятся в системах ограниченного доступа, включая «Google
                    Drive», «AmoCRM».
                </p>

                <h3 className="text-xl md:text-2xl font-bold mt-6 mb-4 text-left">Рекламные сообщения</h3>
                <p className="mb-3">
                    <span className="font-semibold">4.11</span> Пользователю могут направляться рекламные
                    сообщения по e‑mail и/или телефону.
                </p>
                <p className="mb-6">
                    <span className="font-semibold">4.12</span> Отказ от рассылки — письмом с пометкой «Отказ
                    от рекламных сообщений» на{" "}
                    <a href="mailto:famlink.power.kursk@mail.ru" className="text-blue-700 underline">
                        famlink.power.kursk@mail.ru
                    </a>
                    .
                </p>

                <h3 className="text-xl md:text-2xl font-bold mt-6 mb-4 text-left">Обезличенные данные</h3>
                <p className="mb-3">
                    <span className="font-semibold">4.13</span> Собираются технические данные (действия на
                    сайте, IP, домен, тип браузера и ОС, геоданные, cookie, данные Google Analytics,
                    Яндекс.Метрика) — в обезличенном виде.
                </p>
                <p className="mb-3">
                    <span className="font-semibold">4.14</span> Основание — согласие Пользователя, выраженное
                    продолжением использования Сайта после предупреждения.
                </p>
                <p className="mb-6">
                    <span className="font-semibold">4.15</span> При запрете использования таких данных
                    отдельные функции Сайта могут быть недоступны.
                </p>
            </section>

            {/* 5. Согласие */}
            <section aria-labelledby="sec-5">
                <h2 id="sec-5" className="text-2xl md:text-3xl font-bold mt-10 mb-6 text-left">
                    5. Подтверждение согласия на Обработку персональных данных
                </h2>

                <p className="mb-3">
                    <span className="font-semibold">5.1</span> Персональные данные предоставляются
                    Пользователем добровольно.
                </p>
                <p className="mb-3">
                    <span className="font-semibold">5.2</span> Отправляя данные через Формы, Пользователь
                    принимает Политику и даёт согласие на обработку ПД.
                </p>
                <p className="mb-3">
                    <span className="font-semibold">5.3</span> Подтверждение согласия — отметка в чек‑боксе:
                    <em>
                        «Отправляя данные, вы даёте согласие на обработку персональных данных и соглашаетесь с
                        политикой конфиденциальности».
                    </em>
                </p>
                <p className="mb-3">
                    <span className="font-semibold">5.4</span> Согласие действует бессрочно.
                </p>
                <p className="mb-6">
                    <span className="font-semibold">5.5</span> Отзыв согласия — письмом на{" "}
                    <a href="mailto:famlink.power.kursk@mail.ru" className="text-blue-700 underline">
                        famlink.power.kursk@mail.ru
                    </a>
                    .
                </p>
            </section>

            {/* 6. Ответственность */}
            <section aria-labelledby="sec-6">
                <h2 id="sec-6" className="text-2xl md:text-3xl font-bold mt-10 mb-6 text-left">
                    6. Ответственность Компании
                </h2>

                <p className="mb-3">
                    <span className="font-semibold">6.1</span> Компания несёт ответственность за убытки,
                    понесённые Пользователем в связи с неправомерным использованием ПД, в соответствии с
                    законодательством РФ.
                </p>

                <p className="mb-2">
                    <span className="font-semibold">6.2</span> В случае утраты/разглашения ПД Компания не
                    несёт ответственности, если данные:
                </p>
                <ul className="list-disc pl-6 space-y-2 mb-4">
                    <li>стали публичным достоянием до их утраты и (или) разглашения;</li>
                    <li>были получены от третьей стороны до момента их получения Компанией;</li>
                    <li>были разглашены с согласия Пользователя или предоставлены им для общего доступа.</li>
                </ul>

                <p className="mb-2">
                    <span className="font-semibold">6.3</span> Пользователь предупреждён, что:
                </p>
                <ul className="list-disc pl-6 space-y-2 mb-6">
                    <li>
                        Компания не несёт ответственности за внешние ресурсы, ссылки на которые могут
                        содержаться на Сайте. Информация на сторонних сайтах не является дополнением к данному
                        Сайту;
                    </li>
                    <li>
                        Сайт или его часть могут сопровождаться рекламой; Компания не несёт ответственности и
                        не имеет обязательств в связи с такой рекламой.
                    </li>
                </ul>
            </section>

            {/* 7. Дополнительные условия */}
            <section aria-labelledby="sec-7">
                <h2 id="sec-7" className="text-2xl md:text-3xl font-bold mt-10 mb-6 text-left">
                    7. Дополнительные условия
                </h2>

                <p className="mb-3">
                    <span className="font-semibold">7.1</span> Компания вправе изменять Политику. Актуальная
                    редакция вступает в силу с момента размещения. При несогласии Пользователь обязан
                    прекратить использование Сайта. Действующая редакция всегда доступна на странице:{" "}
                    <a
                        href="https://e-devservice.ru/"
                        target="_blank"
                        rel="noreferrer"
                        className="text-blue-700 underline"
                    >
                        https://e-devservice.ru/
                    </a>
                    .
                </p>

                <p className="mb-3">
                    <span className="font-semibold">7.2</span> Признание судом какого‑либо положения Политики
                    недействительным не влечёт недействительности иных положений.
                </p>

                <p className="mb-6">
                    <span className="font-semibold">7.3</span> Запросы по условиям Обработки ПД направляются
                    на адрес электронной почты{" "}
                    <a href="mailto:famlink.power.kursk@mail.ru" className="text-blue-700 underline">
                        famlink.power.kursk@mail.ru
                    </a>
                    . Срок рассмотрения — до 30 календарных дней.
                </p>
            </section>

            {/* 8. Реквизиты */}
            <section aria-labelledby="sec-8">
                <h2 id="sec-8" className="text-2xl md:text-3xl font-bold mt-10 mb-6 text-left">
                    8. Реквизиты Компании
                </h2>

                <p>ИП Сергеев Артём Игоревич</p>
                <p>ИНН: 463249348400</p>
                <p>ОГРНИП: 325460000026418</p>
                <p>Адрес: 305040, г. Курск, ул. Студенческая, д. 8, кв. 29</p>
                <p>
                    e‑mail:{" "}
                    <a href="mailto:famlink.power.kursk@mail.ru" className="text-blue-700 underline">
                        famlink.power.kursk@mail.ru
                    </a>
                </p>

                <p className="text-sm text-gray-500 mt-8">Последнее обновление: 27 июля 2025 г.</p>
            </section>

            <div className="mt-10">
                <Link to="/" className="text-blue-700 underline">
                    ← Вернуться на главную
                </Link>
            </div>
        </main>
    );
};

export default PolicyPage;
