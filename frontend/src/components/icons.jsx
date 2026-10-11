import React from "react";

/* Set de iconos SVG propio SVSP (trazo, sin emojis).
   Uso: <Icon name="shield" size={18} className="..." />
   El color se hereda con `color` (currentColor). */

const PATHS = {
  grid: (
    <React.Fragment>
      <rect x="3.5" y="3.5" width="7" height="7" rx="1.8" />
      <rect x="13.5" y="3.5" width="7" height="7" rx="1.8" />
      <rect x="3.5" y="13.5" width="7" height="7" rx="1.8" />
      <rect x="13.5" y="13.5" width="7" height="7" rx="1.8" />
    </React.Fragment>
  ),
  clock: (
    <React.Fragment>
      <circle cx="12" cy="12" r="8.5" />
      <path d="M12 7.5V12l3 2" />
    </React.Fragment>
  ),
  timer: (
    <React.Fragment>
      <circle cx="12" cy="13.5" r="7.5" />
      <path d="M12 10v3.5l2.5 1.5M9.5 2.5h5M12 2.5V6" />
    </React.Fragment>
  ),
  users: (
    <React.Fragment>
      <circle cx="9" cy="8" r="3.5" />
      <path d="M2.8 19.5c.8-3.2 3.3-5 6.2-5s5.4 1.8 6.2 5" />
      <path d="M15.5 5.2a3.5 3.5 0 0 1 0 5.9M17.8 14.9c2 .7 3.1 2.3 3.5 4.6" />
    </React.Fragment>
  ),
  userPlus: (
    <React.Fragment>
      <circle cx="10" cy="8" r="3.8" />
      <path d="M3.5 20c.9-3.6 3.5-5.5 6.5-5.5 1.2 0 2.4.3 3.3.9" />
      <path d="M18.5 14.5v6M15.5 17.5h6" />
    </React.Fragment>
  ),
  shield: (
    <React.Fragment>
      <path d="M12 2.8 19 6v6c0 5-3.4 8.3-7 9.2C8.4 20.3 5 17 5 12V6l7-3.2Z" />
      <path d="m9.2 11.8 2 2 3.6-3.8" />
    </React.Fragment>
  ),
  clipboard: (
    <React.Fragment>
      <rect x="5" y="4.5" width="14" height="16.5" rx="2.5" />
      <path d="M9 4.5V3.2A1.2 1.2 0 0 1 10.2 2h3.6A1.2 1.2 0 0 1 15 3.2v1.3" />
      <path d="M8.8 10.5h6.4M8.8 14h6.4M8.8 17.5h4" />
    </React.Fragment>
  ),
  chart: (
    <React.Fragment>
      <path d="M4 4v15.5a.5.5 0 0 0 .5.5H20" />
      <path d="M8.5 15.5v-4M12.5 15.5V8M16.5 15.5v-6.5" />
    </React.Fragment>
  ),
  search: (
    <React.Fragment>
      <circle cx="11" cy="11" r="6.5" />
      <path d="m16 16 4.5 4.5" />
    </React.Fragment>
  ),
  check: <path d="m5 12.5 4.5 4.5L19 7.5" />,
  xCircle: (
    <React.Fragment>
      <circle cx="12" cy="12" r="8.5" />
      <path d="m9.5 9.5 5 5M14.5 9.5l-5 5" />
    </React.Fragment>
  ),
  chevronRight: <path d="m9.5 6 6 6-6 6" />,
  qr: (
    <React.Fragment>
      <rect x="3.5" y="3.5" width="7" height="7" rx="1.2" />
      <rect x="13.5" y="3.5" width="7" height="7" rx="1.2" />
      <rect x="3.5" y="13.5" width="7" height="7" rx="1.2" />
      <path d="M13.5 13.5h3v3h-3zM20.5 13.5v.01M13.5 20.5v.01M17 17h3.5v3.5" />
    </React.Fragment>
  ),
  upload: (
    <React.Fragment>
      <path d="M12 15.5v-11M7.5 8 12 3.5 16.5 8" />
      <path d="M4.5 15.5v4a1.5 1.5 0 0 0 1.5 1.5h12a1.5 1.5 0 0 0 1.5-1.5v-4" />
    </React.Fragment>
  ),
  download: (
    <React.Fragment>
      <path d="M12 3.5v11M7.5 11 12 15.5 16.5 11" />
      <path d="M4.5 15.5v4a1.5 1.5 0 0 0 1.5 1.5h12a1.5 1.5 0 0 0 1.5-1.5v-4" />
    </React.Fragment>
  ),
  memo: (
    <React.Fragment>
      <path d="M6 2.8h9L20 7.8V21a1 1 0 0 1-1 1H6a1 1 0 0 1-1-1V3.8a1 1 0 0 1 1-1Z" />
      <path d="M14.5 2.8v5.5H20M9 13h6M9 16.5h6" />
    </React.Fragment>
  ),
  key: (
    <React.Fragment>
      <circle cx="8.5" cy="12" r="4.5" />
      <path d="M12.5 12H21M17.5 12v3.5M20.5 12v2.5" />
    </React.Fragment>
  ),
  plus: <path d="M12 5v14M5 12h14" />,
  pencil: (
    <React.Fragment>
      <path d="m14.5 5.5 4 4L8 20l-4.7.7L4 16l10.5-10.5Z" />
      <path d="m13 7 4 4" />
    </React.Fragment>
  ),
  logout: (
    <React.Fragment>
      <path d="M14 4h-8a1 1 0 0 0-1 1v14a1 1 0 0 0 1 1h8" />
      <path d="m10 12 9-.01M18.5 8.5 22 12l-3.5 3.5" />
    </React.Fragment>
  ),
};

export default function Icon({ name, size = 18, className = "", strokeWidth = 1.8 }) {
  return (
    <svg
      className={`svsp-icon ${className}`}
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={strokeWidth}
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      {PATHS[name] || PATHS.grid}
    </svg>
  );
}
