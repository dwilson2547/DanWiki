import { Link, useNavigate } from 'react-router-dom';
import { Home, ArrowLeft, FileQuestion } from 'lucide-react';

export default function NotFound() {
  const navigate = useNavigate();

  return (
    <div style={{ 
      minHeight: '100vh', 
      background: 'var(--bg)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '2rem'
    }}>
      <div style={{ 
        maxWidth: '600px', 
        width: '100%',
        textAlign: 'center'
      }}>
        {/* Icon */}
        <div style={{ 
          display: 'flex', 
          justifyContent: 'center', 
          marginBottom: '2rem' 
        }}>
          <div style={{ 
            background: 'var(--card)',
            padding: '2rem',
            borderRadius: '50%',
            border: '2px solid var(--border)'
          }}>
            <FileQuestion size={64} color="var(--muted)" />
          </div>
        </div>

        {/* 404 Text */}
        <h1 style={{ 
          fontSize: '4rem', 
          fontWeight: 'bold',
          margin: '0 0 1rem 0',
          color: 'var(--text)'
        }}>
          404
        </h1>

        {/* Message */}
        <h2 style={{ 
          fontSize: '1.5rem', 
          margin: '0 0 1rem 0',
          color: 'var(--text)'
        }}>
          Page Not Found
        </h2>

        <p style={{ 
          color: 'var(--muted)',
          fontSize: '1rem',
          marginBottom: '2rem',
          lineHeight: '1.6'
        }}>
          The page you're looking for doesn't exist or may have been moved. 
          This could be due to a broken link in the wiki content or an incorrect URL.
        </p>

        {/* Action Buttons */}
        <div style={{ 
          display: 'flex', 
          gap: '1rem',
          justifyContent: 'center',
          flexWrap: 'wrap'
        }}>
          <button
            onClick={() => navigate(-1)}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
              padding: '0.75rem 1.5rem',
              background: 'var(--card)',
              color: 'var(--text)',
              border: '1px solid var(--border)',
              borderRadius: '8px',
              fontSize: '1rem',
              cursor: 'pointer',
              transition: 'all 0.2s'
            }}
            onMouseEnter={(e) => {
              e.target.style.background = 'var(--hover)';
              e.target.style.borderColor = 'var(--primary)';
            }}
            onMouseLeave={(e) => {
              e.target.style.background = 'var(--card)';
              e.target.style.borderColor = 'var(--border)';
            }}
          >
            <ArrowLeft size={20} />
            Go Back
          </button>

          <Link
            to="/"
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
              padding: '0.75rem 1.5rem',
              background: 'var(--primary)',
              color: 'white',
              border: 'none',
              borderRadius: '8px',
              fontSize: '1rem',
              textDecoration: 'none',
              transition: 'all 0.2s'
            }}
            onMouseEnter={(e) => {
              e.target.style.opacity = '0.9';
            }}
            onMouseLeave={(e) => {
              e.target.style.opacity = '1';
            }}
          >
            <Home size={20} />
            Go to Home
          </Link>
        </div>

        {/* Additional Help */}
        <div style={{ 
          marginTop: '3rem',
          padding: '1.5rem',
          background: 'var(--card)',
          border: '1px solid var(--border)',
          borderRadius: '8px',
          textAlign: 'left'
        }}>
          <h3 style={{ 
            fontSize: '1rem',
            margin: '0 0 0.75rem 0',
            color: 'var(--text)'
          }}>
            What can you do?
          </h3>
          <ul style={{ 
            margin: 0,
            paddingLeft: '1.5rem',
            color: 'var(--muted)',
            lineHeight: '1.8'
          }}>
            <li>Check if the URL is spelled correctly</li>
            <li>Go back to the previous page</li>
            <li>Visit the home page to browse available wikis</li>
            <li>Use the search feature to find what you're looking for</li>
          </ul>
        </div>
      </div>
    </div>
  );
}
