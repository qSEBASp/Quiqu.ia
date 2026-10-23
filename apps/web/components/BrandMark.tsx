export function BrandMark({ className = "" }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 128 128"
      className={className}
      aria-hidden="true"
      focusable="false"
    >
      <defs>
        <linearGradient
          id="quiqu-mark-bg"
          x1="18"
          y1="12"
          x2="112"
          y2="120"
          gradientUnits="userSpaceOnUse"
        >
          <stop stopColor="#ff7580" />
          <stop offset="0.48" stopColor="#ff4655" />
          <stop offset="1" stopColor="#a9152d" />
        </linearGradient>
        <linearGradient
          id="quiqu-mark-q"
          x1="34"
          y1="24"
          x2="94"
          y2="98"
          gradientUnits="userSpaceOnUse"
        >
          <stop stopColor="#ffffff" />
          <stop offset="1" stopColor="#ffe3e6" />
        </linearGradient>
        <linearGradient
          id="quiqu-mark-tail"
          x1="82"
          y1="78"
          x2="110"
          y2="106"
          gradientUnits="userSpaceOnUse"
        >
          <stop stopColor="#d8b4fe" />
          <stop offset="0.45" stopColor="#a855f7" />
          <stop offset="1" stopColor="#6d28d9" />
        </linearGradient>
        <radialGradient id="quiqu-mark-glow" cx="0.78" cy="0.82" r="0.54">
          <stop stopColor="#a855f7" stopOpacity="0.48" />
          <stop offset="1" stopColor="#a855f7" stopOpacity="0" />
        </radialGradient>
        <clipPath id="quiqu-mark-card">
          <rect width="128" height="128" rx="30" />
        </clipPath>
      </defs>

      <g clipPath="url(#quiqu-mark-card)">
        <rect width="128" height="128" fill="url(#quiqu-mark-bg)" />
        <circle cx="98" cy="104" r="48" fill="url(#quiqu-mark-glow)" />
        <ellipse
          cx="38"
          cy="20"
          rx="54"
          ry="28"
          fill="#ffffff"
          opacity="0.13"
          transform="rotate(-18 38 20)"
        />
        <path
          d="M-8 108c26-12 46-2 68-9 21-7 32-20 52-19 14 1 23 6 30 12v44H-8z"
          fill="#6d28d9"
          opacity="0.18"
        />
      </g>

      <circle
        cx="64"
        cy="60"
        r="33"
        fill="none"
        stroke="url(#quiqu-mark-q)"
        strokeWidth="15"
      />
      <path
        d="M82 78 107 103"
        stroke="url(#quiqu-mark-tail)"
        strokeWidth="15"
        strokeLinecap="round"
      />

      <rect
        x="2.5"
        y="2.5"
        width="123"
        height="123"
        rx="27.5"
        fill="none"
        stroke="#ffffff"
        strokeOpacity="0.16"
        strokeWidth="2"
      />
    </svg>
  );
}
