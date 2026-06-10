import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import ru from './ru.json';
import kz from './kz.json';

const stored = localStorage.getItem('lang');
const lng = stored === 'kz' || stored === 'ru' ? stored : 'ru';

i18n.use(initReactI18next).init({
  resources: {
    ru: { translation: ru },
    kz: { translation: kz },
  },
  lng,
  fallbackLng: 'ru',
  interpolation: { escapeValue: false },
});

export default i18n;
