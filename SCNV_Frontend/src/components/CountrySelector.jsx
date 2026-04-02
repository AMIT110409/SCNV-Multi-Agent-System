import React, { useState, useEffect } from 'react';
import { Globe, ChevronDown } from 'lucide-react';
import { API_URL, STORAGE_KEYS } from '../config/constants';

const COUNTRY_NAMES = {
  BE: '🇧🇪 Belgium', NL: '🇳🇱 Netherlands', DE: '🇩🇪 Germany', GB: '🇬🇧 United Kingdom',
  FR: '🇫🇷 France', ES: '🇪🇸 Spain', IT: '🇮🇹 Italy', PL: '🇵🇱 Poland',
  SE: '🇸🇪 Sweden', US: '🇺🇸 United States', CN: '🇨🇳 China', IN: '🇮🇳 India',
  SG: '🇸🇬 Singapore', BR: '🇧🇷 Brazil', MX: '🇲🇽 Mexico', JP: '🇯🇵 Japan',
  AU: '🇦🇺 Australia', HK: '🇭🇰 Hong Kong', TR: '🇹🇷 Turkey', ZA: '🇿🇦 South Africa',
};

function CountrySelector({ selectedCountry, onCountryChange }) {
  const [countries, setCountries] = useState([]);
  const [isOpen, setIsOpen] = useState(false);

  useEffect(() => {
    const token = localStorage.getItem(STORAGE_KEYS.TOKEN);
    fetch(`${API_URL}/api/kpi/countries`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((r) => r.json())
      .then((data) => setCountries(data.countries || []))
      .catch(console.error);
  }, []);

  const label = selectedCountry
    ? COUNTRY_NAMES[selectedCountry] || selectedCountry
    : '🌍 All Countries';

  return (
    <div className="country-selector" style={{ position: 'relative' }}>
      <button
        className="country-selector__btn"
        onClick={() => setIsOpen(!isOpen)}
        id="country-selector-btn"
      >
        <Globe size={16} />
        <span>{label}</span>
        <ChevronDown size={14} style={{ transform: isOpen ? 'rotate(180deg)' : 'none', transition: 'transform 0.2s' }} />
      </button>

      {isOpen && (
        <div className="country-selector__dropdown">
          <button
            className={`country-selector__option ${!selectedCountry ? 'country-selector__option--active' : ''}`}
            onClick={() => { onCountryChange(null); setIsOpen(false); }}
          >
            🌍 All Countries
          </button>
          {countries.map((cc) => (
            <button
              key={cc}
              className={`country-selector__option ${selectedCountry === cc ? 'country-selector__option--active' : ''}`}
              onClick={() => { onCountryChange(cc); setIsOpen(false); }}
            >
              {COUNTRY_NAMES[cc] || cc}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

export default CountrySelector;
