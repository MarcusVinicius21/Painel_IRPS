import {createRoot} from 'react-dom/client';
import {ApiProvider} from './api';
import App from './App';
import './styles.css';
import './integration.css';
createRoot(document.getElementById('root')!).render(<ApiProvider><App/></ApiProvider>);
