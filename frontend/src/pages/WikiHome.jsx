import { useOutletContext, Link } from 'react-router-dom';
import { FileText, Plus, Clock, User } from 'lucide-react';

export default function WikiHome() {
  const { wiki, pages } = useOutletContext();

  // Get recent pages (flatten and sort by updated_at)
  const flattenPages = (pages) => {
    let result = [];
    for (const page of pages) {
      result.push(page);
      if (page.children) {
        result = result.concat(flattenPages(page.children));
      }
    }
    return result;
  };

  const allPages = flattenPages(pages);
  const recentPages = [...allPages]
    .sort((a, b) => new Date(b.updated_at) - new Date(a.updated_at))
    .slice(0, 5);

  return (
    <div className="page-content">
      <div className="page-header">
        <h1 className="page-title">{wiki?.name}</h1>
        {wiki?.description && (
          <p className="text-secondary mt-2">{wiki.description}</p>
        )}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '2rem' }}>
        {/* Quick Stats */}
        <div className="card">
          <div className="card-header">
            <h3 className="font-semibold">Overview</h3>
          </div>
          <div className="card-body">
            <div className="flex items-center gap-3 mb-4">
              <div className="p-3 rounded-lg" style={{ background: 'var(--background)' }}>
                <FileText size={24} style={{ color: 'var(--primary)' }} />
              </div>
              <div>
                <div className="text-2xl font-semibold">{allPages.length}</div>
                <div className="text-sm text-secondary">Total pages</div>
              </div>
            </div>
            
            <div className="text-sm text-secondary">
              <div className="flex items-center gap-2 mb-1">
                <User size={14} />
                <span>Created by {wiki?.owner?.display_name || wiki?.owner?.username}</span>
              </div>
              <div className="flex items-center gap-2">
                <Clock size={14} />
                <span>Last updated {new Date(wiki?.updated_at).toLocaleDateString()}</span>
              </div>
            </div>
          </div>
        </div>

        {/* Recent Pages */}
        <div className="card">
          <div className="card-header">
            <h3 className="font-semibold">Recent Pages</h3>
          </div>
          <div className="card-body" style={{ padding: 0 }}>
            {recentPages.length === 0 ? (
              <div className="p-6 text-center text-secondary">
                <FileText size={32} style={{ margin: '0 auto 0.5rem', opacity: 0.5 }} />
                <p className="text-sm">No pages yet</p>
              </div>
            ) : (
              <ul style={{ listStyle: 'none' }}>
                {recentPages.map(page => (
                  <li key={page.id} style={{ borderBottom: '1px solid var(--border)' }}>
                    <Link
                      to={`/wiki/${wiki.id}/page/${page.id}`}
                      className="flex items-center justify-between p-3"
                      style={{ color: 'var(--text)', textDecoration: 'none' }}
                    >
                      <div className="flex items-center gap-2">
                        <FileText size={16} className="text-secondary" />
                        <span>{page.title}</span>
                      </div>
                      <span className="text-xs text-secondary">
                        {new Date(page.updated_at).toLocaleDateString()}
                      </span>
                    </Link>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>
      </div>

      {/* Page Tree */}
      <div className="card mt-6">
        <div className="card-header">
          <h3 className="font-semibold">All Pages</h3>
        </div>
        <div className="card-body">
          {pages.length === 0 ? (
            <div className="empty-state">
              <FileText size={48} style={{ margin: '0 auto 1rem', opacity: 0.5 }} />
              <h4 className="font-semibold mb-2">No pages yet</h4>
              <p className="text-secondary text-sm mb-4">
                Create your first page to get started documenting your knowledge
              </p>
            </div>
          ) : (
            <PageList pages={pages} wikiId={wiki.id} />
          )}
        </div>
      </div>
    </div>
  );
}

function PageList({ pages, wikiId, level = 0 }) {
  return (
    <ul style={{ listStyle: 'none', marginLeft: level * 20 }}>
      {pages.map(page => (
        <li key={page.id} className="mb-1">
          <Link
            to={`/wiki/${wikiId}/page/${page.id}`}
            className="flex items-center gap-2 py-1 px-2 rounded"
            style={{ color: 'var(--text)', textDecoration: 'none' }}
          >
            <FileText size={14} className="text-secondary" />
            <span>{page.title}</span>
          </Link>
          {page.children && page.children.length > 0 && (
            <PageList pages={page.children} wikiId={wikiId} level={level + 1} />
          )}
        </li>
      ))}
    </ul>
  );
}
