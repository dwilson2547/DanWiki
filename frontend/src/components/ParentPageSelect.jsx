import Select from 'react-select';

/**
 * ParentPageSelect - A searchable dropdown for selecting parent pages
 * Features:
 * - Shows page hierarchy with visual depth indicators
 * - Searchable by page title
 * - Clear indication of page nesting level
 */
export default function ParentPageSelect({ pages, value, onChange, placeholder = "None (top level)", disabled = false }) {
  // Flatten the page tree to include depth information
  const flattenPages = (pages, level = 0) => {
    let result = [];
    for (const page of pages) {
      result.push({ ...page, level });
      if (page.children) {
        result = result.concat(flattenPages(page.children, level + 1));
      }
    }
    return result;
  };

  const flatPages = flattenPages(pages);

  // Convert flat pages to react-select options format
  const options = [
    { value: null, label: placeholder, level: 0 },
    ...flatPages.map(page => ({
      value: page.id,
      label: page.title,
      level: page.level
    }))
  ];

  // Find the selected option
  const selectedOption = options.find(opt => opt.value === value) || options[0];

  // Custom option formatting to show depth
  const formatOptionLabel = ({ label, level }) => {
    const indent = '└─'.repeat(level);
    const spacing = '\u00A0'.repeat(level * 2); // Non-breaking spaces for indentation
    
    return (
      <div style={{ 
        display: 'flex', 
        alignItems: 'center',
        fontFamily: 'monospace'
      }}>
        {level > 0 && (
          <span style={{ 
            color: 'var(--text-secondary, #666)', 
            marginRight: '0.5rem',
            fontSize: '0.85em'
          }}>
            {indent}
          </span>
        )}
        <span>{label}</span>
      </div>
    );
  };

  // Custom styles to match the existing theme
  const customStyles = {
    control: (provided, state) => ({
      ...provided,
      backgroundColor: 'var(--surface, #fff)',
      borderColor: state.isFocused ? 'var(--primary, #2563eb)' : 'var(--border, #ddd)',
      borderRadius: '0.375rem',
      minHeight: '38px',
      fontSize: '0.875rem',
      boxShadow: state.isFocused ? '0 0 0 1px var(--primary, #2563eb)' : 'none',
      '&:hover': {
        borderColor: 'var(--primary, #2563eb)'
      }
    }),
    menuPortal: (provided) => ({
      ...provided,
      zIndex: 10000
    }),
    menu: (provided) => ({
      ...provided,
      backgroundColor: 'var(--surface, #fff)',
      border: '1px solid var(--border, #ddd)',
      borderRadius: '0.375rem',
      boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
    }),
    option: (provided, state) => ({
      ...provided,
      backgroundColor: state.isSelected 
        ? 'var(--primary, #2563eb)' 
        : state.isFocused 
          ? 'var(--surface-hover, #1d4ed8)' 
          : 'transparent',
      color: state.isSelected ? '#ffffff' : 'var(--text)',
      fontSize: '0.875rem',
      padding: '0.5rem 0.75rem',
      cursor: 'pointer',
      '&:active': {
        backgroundColor: 'var(--primary-dark, #1d4ed8)',
        color: '#ffffff'
      }
    }),
    singleValue: (provided) => ({
      ...provided,
      color: 'var(--text, #000)',
      fontSize: '0.875rem'
    }),
    input: (provided) => ({
      ...provided,
      color: 'var(--text, #000)',
      fontSize: '0.875rem'
    }),
    placeholder: (provided) => ({
      ...provided,
      color: 'var(--text-secondary, #666)',
      fontSize: '0.875rem'
    }),
    dropdownIndicator: (provided) => ({
      ...provided,
      color: 'var(--text-secondary, #666)',
      '&:hover': {
        color: 'var(--text, #000)'
      }
    }),
    clearIndicator: (provided) => ({
      ...provided,
      color: 'var(--text-secondary, #666)',
      '&:hover': {
        color: 'var(--text, #000)'
      }
    })
  };

  return (
    <Select
      options={options}
      value={selectedOption}
      onChange={(option) => onChange(option?.value ?? null)}
      formatOptionLabel={formatOptionLabel}
      styles={customStyles}
      isDisabled={disabled}
      isClearable={false}
      isSearchable={true}
      placeholder={placeholder}
      menuPlacement="auto"
      menuPortalTarget={document.body}
      maxMenuHeight={300}
    />
  );
}
