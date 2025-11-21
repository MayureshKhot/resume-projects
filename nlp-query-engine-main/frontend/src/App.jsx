import { useState, useEffect } from 'react';
import './App.css';
import './components/DocumentResults.css';

const API_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';

// --- Display Components for Schema & Query Results ---

const SchemaDisplay = ({ schema }) => {
  if (!schema) return null;
  if (schema.error) return <div className="alert alert-danger">Error: {schema.error}</div>;
  
  // Handle the actual API response structure
  const schemaData = schema.schema?.schema || schema.schema;
  if (!schemaData || Object.keys(schemaData).length === 0) return null;

  return (
    <div className="results-container">
      {Object.entries(schemaData).map(([tableName, tableDetails]) => (
        <div key={tableName} className="mb-4">
          <h4 style={{ color: 'var(--text-secondary)', fontWeight: 400 }}>Table: <strong style={{color: 'var(--text-primary)', fontWeight: 600}}>{tableName}</strong></h4>
          <table>
            <thead>
              <tr><th>Column Name</th><th>Data Type</th></tr>
            </thead>
            <tbody>
              {tableDetails.columns && tableDetails.columns.map ? 
                tableDetails.columns.map(col => <tr key={col.name}><td>{col.name}</td><td>{col.type}</td></tr>) :
                <tr><td colSpan="2">No columns found</td></tr>
              }
            </tbody>
          </table>
        </div>
      ))}
    </div>
  );
};

const ResultsDisplay = ({ queryResult }) => {
  if (!queryResult) return null;
  if (queryResult.error) return <div className="alert alert-danger">{queryResult.error}</div>;

  const { query_type, results, execution_time } = queryResult;

  if (!results || (Array.isArray(results) && results.length === 0)) {
    const message = query_type === 'sql' ? "Query returned no results." : "No matching documents found.";
    return <div className="results-container alert alert-info">{message}</div>;
  }

  if (query_type === 'sql') {
    if (results.length === 0) {
      return <div className="results-container alert alert-info">No SQL results found.</div>;
    }
    
    const headers = Object.keys(results[0]);
    return (
      <div className="results-container">
        <div className="result-header">
          <h4>SQL Results ({results.length} rows)</h4>
          <span className="execution-time">Executed in {execution_time?.toFixed(3)}s</span>
        </div>
        <table>
          <thead><tr>{headers.map(h => <th key={h}>{h}</th>)}</tr></thead>
          <tbody>
            {results.map((row, i) => <tr key={i}>{headers.map(h => <td key={h}>{row[h]}</td>)}</tr>)}
          </tbody>
        </table>
      </div>
    );
  }

  if (query_type === 'document') {
    return (
      <div className="results-container">
        <div className="result-header">
          <h4>Document Results ({results.length} matches)</h4>
          <span className="execution-time">Executed in {execution_time?.toFixed(3)}s</span>
        </div>
        {results.map((doc, i) => (
          <div className="doc-card" key={i}>
            <div className="doc-card-header">
              <div className="doc-title">
                <strong>{doc.source}</strong> 
                <span className="doc-type">{doc.content_type}</span>
              </div>
              <div className="doc-meta">
                Match Score: {doc.similarity_score?.toFixed(3)}
                {doc.last_updated && 
                  <span className="doc-date">
                    Last Updated: {new Date(doc.last_updated).toLocaleDateString()}
                  </span>
                }
              </div>
            </div>
            <div className="doc-card-body">
              <div className="doc-preview">
                <h5>Matched Content:</h5>
                {doc.content_preview}
              </div>
              <div className="doc-full">
                <h5>Full Document:</h5>
                <pre className="doc-content">{doc.full_document}</pre>
              </div>
            </div>
          </div>
        ))}
      </div>
    );
  }

  if (query_type === 'hybrid') {
    const { sql_results, document_results, sql_count, document_count } = results;
    
    return (
      <div className="results-container">
        <div className="result-header">
          <h4>Hybrid Search Results</h4>
          <span className="execution-time">Executed in {execution_time?.toFixed(3)}s</span>
        </div>
        
        <div className="hybrid-results">
          <div className="sql-section">
            <h5>Database Results ({sql_count} rows)</h5>
            {sql_results && sql_results.length > 0 ? (
              <table>
                <thead>
                  <tr>{Object.keys(sql_results[0]).map(h => <th key={h}>{h}</th>)}</tr>
                </thead>
                <tbody>
                  {sql_results.map((row, i) => (
                    <tr key={i}>
                      {Object.keys(row).map(h => <td key={h}>{row[h]}</td>)}
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : (
              <p className="no-results">No database results found.</p>
            )}
          </div>
          
          <div className="document-section">
            <h5>Document Results ({document_count} matches)</h5>
            {document_results && document_results.length > 0 ? (
              document_results.map((doc, i) => (
                <div className="doc-card" key={i}>
                  <div className="doc-card-header">
                    {doc.source} (Score: {doc.similarity_score?.toFixed(3)})
                  </div>
                  <div className="doc-card-body">{doc.content_preview}</div>
                </div>
              ))
            ) : (
              <p className="no-results">No document results found.</p>
            )}
          </div>
        </div>
      </div>
    );
  }

  return null;
};

// --- Main App Component ---

function App() {
  const [connectionString, setConnectionString] = useState('sqlite:///./test.db');
  const [query, setQuery] = useState('');
  const [documentQuery, setDocumentQuery] = useState('');
  const [selectedFiles, setSelectedFiles] = useState(null);
  const [fileName, setFileName] = useState('No file chosen');
  const [employeeId, setEmployeeId] = useState('');
  
  const [schema, setSchema] = useState(null);
  const [uploadStatus, setUploadStatus] = useState('');
  const [queryResult, setQueryResult] = useState(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleFileChange = (e) => {
    setSelectedFiles(e.target.files);
    setFileName(e.target.files.length > 0 ? `${e.target.files.length} file(s) selected` : 'No file chosen');
  };

  const handleApiCall = async (endpoint, options, onSuccess, onError) => {
    setIsLoading(true);
    // Clear previous results on a new action
    setSchema(null);
    setUploadStatus('');
    setQueryResult(null);
    try {
      const url = `${API_URL}${endpoint}`;
      console.log('Making API call to:', url);
      console.log('With options:', {
        ...options,
        body: options.body instanceof FormData ? 
          Object.fromEntries(options.body.entries()) : 
          options.body
      });
      
      const response = await fetch(url, {
        ...options,
        credentials: 'include',
      });
      
      console.log('Response status:', response.status);
      console.log('Response headers:', Object.fromEntries(response.headers.entries()));
      
      let data;
      const contentType = response.headers.get('content-type');
      if (contentType && contentType.includes('application/json')) {
        data = await response.json().catch(e => ({ error: 'Failed to parse JSON response' }));
      } else {
        data = await response.text();
        try {
          data = JSON.parse(data);
        } catch (e) {
          console.log('Response is not JSON:', data);
          data = { message: data };
        }
      }
      
      console.log('Response data:', data);
      
      if (!response.ok) {
        throw new Error(data.error || data.detail || `API request failed with status ${response.status}`);
      }
      
      onSuccess(data);
    } catch (error) {
      console.error('API call error:', error);
      onError(error.message);
    }
    setIsLoading(false);
  };

  const handleConnect = (e) => {
    e.preventDefault();
    handleApiCall('/api/connect-database',
      { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ connection_string: connectionString }) },
      (data) => setSchema(data),
      (error) => setSchema({ error })
    );
  };

  const handleUpload = (e) => {
    e.preventDefault();
    if (!selectedFiles || !employeeId) return;
    const formData = new FormData();
    for (let i = 0; i < selectedFiles.length; i++) {
      formData.append('files', selectedFiles[i]);
    }
    formData.append('emp_id', employeeId);
    handleApiCall('/api/upload-documents',
      { 
        method: 'POST', 
        body: formData,
        // Remove the Content-Type header to let the browser set it with the boundary parameter
        headers: {} 
      },
      (data) => {
        setUploadStatus(data.message);
        setEmployeeId(''); // Clear the employee ID after successful upload
        setSelectedFiles(null); // Clear selected files
        setFileName('No file chosen'); // Reset file name display
      },
      (error) => setUploadStatus(`Upload failed: ${error}`)
    );
  };

  const handleQuery = (e, queryType) => {
    e.preventDefault();
    const queryText = queryType === 'sql' ? query : documentQuery;
    
    if (!queryText.trim()) {
      setQueryResult({ error: 'Please enter a query' });
      return;
    }

    const requestBody = {
      query: queryText,
      queryType: queryType,
      use_cache: true
    };

    console.log('Sending query request:', requestBody);
    
    handleApiCall('/api/query',
      { 
        method: 'POST', 
        headers: { 
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        }, 
        body: JSON.stringify(requestBody)
      },
      (data) => {
        console.log('Query response:', data);
        setQueryResult(data);
      },
      (error) => {
        console.error('Query error:', error);
        setQueryResult({ error });
      }
    );
  };

  return (
    <div className="app-container">
      <header className="app-header">
        <svg className="app-header-icon" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M16.886 18.136L14.058 15.308M14.058 15.308C15.1765 14.1895 15.8333 12.6783 15.8333 11.0417C15.8333 7.82487 13.2585 5.25 10.0417 5.25C6.82487 5.25 4.25 7.82487 4.25 11.0417C4.25 14.2585 6.82487 16.8333 10.0417 16.8333C11.6783 16.8333 13.1895 16.1765 14.308 15.058L14.058 15.308Z" stroke="var(--accent-primary)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
          <path d="M19.9998 8.49983H12.0832" stroke="var(--text-secondary)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
          <path d="M19.9998 13.6667H15.8332" stroke="var(--text-secondary)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
        </svg>
        <h1>NLP Query Engine</h1>
      </header>

      <div className="action-card">
        <h2>1. Connect to Database</h2>
        <form onSubmit={handleConnect} className="form-group">
          <input type="text" className="query-input" value={connectionString} onChange={(e) => setConnectionString(e.target.value)} required />
          <button type="submit" className="glow-button primary" disabled={isLoading}>Connect</button>
        </form>
        {schema && <SchemaDisplay schema={schema} />}
      </div>

      <div className="action-card">
        <h2>2. Upload Documents</h2>
        <form onSubmit={handleUpload} className="form-group">
          <div className="file-input-wrapper">
            <input type="file" className="file-input" onChange={handleFileChange} multiple required />
            <span className={`file-input-label ${selectedFiles ? 'active' : ''}`}>{fileName}</span>
          </div>
          <input 
            type="text" 
            pattern="[0-9]*"
            className="query-input" 
            value={employeeId} 
            onChange={(e) => {
              // Only allow numbers
              const value = e.target.value.replace(/\D/g, '');
              setEmployeeId(value);
            }}
            placeholder="Enter Employee ID (Valid IDs: 101-105)" 
            required 
          />
          <button type="submit" className="glow-button primary" disabled={isLoading || !selectedFiles || !employeeId}>Upload</button>
        </form>
        {uploadStatus && <div className="results-container alert alert-success">{uploadStatus}</div>}
      </div>
      
      <div className="action-card">
        <h2>3. Query Data</h2>
        <div className="query-section">
          <h3>SQL Query</h3>
          <form onSubmit={(e) => {
            e.preventDefault();
            handleQuery(e, 'sql');
          }} className="form-group">
            <input 
              type="text" 
              className="query-input" 
              value={query} 
              onChange={(e) => setQuery(e.target.value)} 
              placeholder="e.g., List all employees and their salaries" 
              required 
            />
            <button type="submit" className="glow-button primary" disabled={isLoading}>Run SQL Query</button>
          </form>
        </div>

        <div className="query-section">
          <h3>Document Search</h3>
          <form onSubmit={(e) => {
            e.preventDefault();
            handleQuery(e, 'document');
          }} className="form-group">
            <input 
              type="text" 
              className="query-input" 
              value={documentQuery} 
              onChange={(e) => setDocumentQuery(e.target.value)} 
              placeholder="e.g., Find resumes with Python experience" 
              required 
            />
            <button type="submit" className="glow-button success" disabled={isLoading}>Search Documents</button>
          </form>
        </div>

        {isLoading && <div className="loader-container"><div className="spinner"></div></div>}
        {queryResult && <ResultsDisplay queryResult={queryResult} />}
      </div>
    </div>
  );
}

export default App;