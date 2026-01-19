import { useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { ChevronRight, ChevronDown, FileText, FolderOpen } from 'lucide-react';

function PageTreeItem({ page, wikiId, level = 0 }) {
  const { pageId } = useParams();
  const [expanded, setExpanded] = useState(true);
  const hasChildren = page.children && page.children.length > 0;
  const isActive = parseInt(pageId) === page.id;

  return (
    <li className="page-tree-item">
      <div className="flex items-center">
        {hasChildren && (
          <button
            className="btn btn-ghost btn-icon btn-sm"
            onClick={() => setExpanded(!expanded)}
            // style={{ marginLeft: level * 8 }}
          >
            {expanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
          </button>
        )}
        {!hasChildren && (
          // <span style={{ width: 28, marginLeft: level * 8 }} />
          <span style={{ width: 28 }} />
        )}
        <Link
          to={`/wiki/${wikiId}/page/${page.id}`}
          className={`page-tree-link flex-1 ${isActive ? 'active' : ''}`}
        >
          {hasChildren ? <FolderOpen size={16} /> : <FileText size={16} />}
          <span className="text-sm">{page.title}</span>
        </Link>
      </div>
      
      {hasChildren && expanded && (
        <ul className="page-tree-children">
          {page.children.map(child => (
            <PageTreeItem
              key={child.id}
              page={child}
              wikiId={wikiId}
              level={level + 1}
            />
          ))}
        </ul>
      )}
    </li>
  );
}

export default function PageTree({ pages, wikiId }) {
  if (!pages || pages.length === 0) {
    return (
      <div className="empty-state p-4">
        <FileText size={32} className="empty-state-icon" style={{ margin: '0 auto' }} />
        <p className="text-sm text-secondary">No pages yet</p>
      </div>
    );
  }

  return (
    <ul className="page-tree">
      {pages.map(page => (
        <PageTreeItem key={page.id} page={page} wikiId={wikiId} />
      ))}
    </ul>
  );
}
