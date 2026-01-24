import { useState, useEffect } from 'react';
import { Users, BookOpen, FileText, Shield, Database, UserCheck } from 'lucide-react';
import { adminAPI } from '../services/api';
import { Link } from 'react-router-dom';

export default function AdminDashboard() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadStats();
  }, []);

  const loadStats = async () => {
    try {
      const response = await adminAPI.getStats();
      setStats(response.data.stats);
    } catch (err) {
      console.error('Failed to load stats:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="loading-container" style={{ minHeight: '400px' }}>
        <div className="spinner" />
      </div>
    );
  }

  const StatCard = ({ icon: Icon, title, value, subtitle, color }) => (
    <div style={{
      background: 'var(--surface)',
      border: '1px solid var(--border)',
      borderRadius: '0.5rem',
      padding: '1.5rem'
    }}>
      <div className="flex items-center gap-3 mb-3">
        <div style={{
          width: '3rem',
          height: '3rem',
          borderRadius: '0.5rem',
          background: color,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: 'white'
        }}>
          <Icon size={24} />
        </div>
        <div>
          <div style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', marginBottom: '0.25rem' }}>
            {title}
          </div>
          <div style={{ fontSize: '1.875rem', fontWeight: 700 }}>
            {value}
          </div>
        </div>
      </div>
      {subtitle && (
        <div style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>
          {subtitle}
        </div>
      )}
    </div>
  );

  return (
    <div style={{ padding: '2rem', maxWidth: 1400, margin: '0 auto' }}>
      <div className="mb-6">
        <h2 style={{ fontSize: '1.875rem', fontWeight: 700, marginBottom: '0.5rem' }}>
          Admin Dashboard
        </h2>
        <p style={{ color: 'var(--text-secondary)' }}>
          System overview and statistics
        </p>
      </div>

      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
        gap: '1.5rem',
        marginBottom: '2rem'
      }}>
        <StatCard
          icon={Users}
          title="Total Users"
          value={stats?.users?.total || 0}
          subtitle={`${stats?.users?.active || 0} active, ${stats?.users?.admins || 0} admins${stats?.users?.pending_approval > 0 ? `, ${stats.users.pending_approval} pending` : ''}`}
          color="var(--primary)"
        />
        
        <StatCard
          icon={BookOpen}
          title="Total Wikis"
          value={stats?.wikis?.total || 0}
          subtitle={`${stats?.wikis?.public || 0} public wikis`}
          color="#10b981"
        />
        
        <StatCard
          icon={FileText}
          title="Total Pages"
          value={stats?.pages?.total || 0}
          subtitle={`${stats?.pages?.pending_embeddings || 0} pending embeddings`}
          color="#f59e0b"
        />
      </div>

      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
        gap: '1.5rem',
        marginBottom: '2rem'
      }}>
        {stats?.users?.pending_approval > 0 && (
          <div style={{
            background: 'var(--surface)',
            border: '1px solid var(--warning)',
            borderRadius: '0.5rem',
            padding: '1.5rem'
          }}>
            <div className="flex items-center gap-3 mb-3">
              <UserCheck size={24} style={{ color: 'var(--warning)' }} />
              <div>
                <div style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', marginBottom: '0.25rem' }}>
                  Pending Approvals
                </div>
                <div style={{ fontSize: '1.5rem', fontWeight: 700 }}>
                  {stats.users.pending_approval}
                </div>
              </div>
            </div>
            <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', marginBottom: '1rem' }}>
              New user registrations waiting for review
            </p>
            <Link
              to="/admin/pending-users"
              className="btn btn-sm"
              style={{ background: 'var(--warning)', color: 'white' }}
            >
              Review Pending Users
            </Link>
          </div>
        )}
        
        {stats?.pages?.pending_embeddings > 0 && (
          <div style={{
            background: 'var(--surface)',
            border: '1px solid var(--border)',
            borderRadius: '0.5rem',
            padding: '1.5rem'
          }}>
            <div className="flex items-center gap-3 mb-3">
              <div style={{
                width: '3rem',
                height: '3rem',
                borderRadius: '0.5rem',
                background: '#f59e0b',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: 'white'
              }}>
                <Database size={24} />
              </div>
              <div>
                <div style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', marginBottom: '0.25rem' }}>
                  Embeddings Needed
                </div>
                <div style={{ fontSize: '1.875rem', fontWeight: 700 }}>
                  {stats?.pages?.pending_embeddings || 0}
                </div>
              </div>
            </div>
            <a 
              href="/admin/embeddings" 
              className="btn btn-primary"
              style={{ width: '100%', marginTop: '1rem', justifyContent: 'center' }}
            >
              Manage Embeddings
            </a>
          </div>
        )}
      </div>

      <div style={{
        background: 'var(--surface)',
        border: '1px solid var(--border)',
        borderRadius: '0.5rem',
        padding: '1.5rem'
      }}>
        <h3 style={{ fontSize: '1.25rem', fontWeight: 600, marginBottom: '1rem' }}>
          Quick Actions
        </h3>
        <div className="flex gap-3 flex-wrap">
          <a href="/admin/users" className="btn btn-primary">
            <Users size={18} />
            Manage Users
          </a>
          <a href="/admin/wikis" className="btn btn-secondary">
            <BookOpen size={18} />
            Manage Wikis
          </a>
          <a href="/admin/embeddings" className="btn btn-secondary">
            <Database size={18} />
            Manage Embeddings
          </a>
        </div>
      </div>
    </div>
  );
}
