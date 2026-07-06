
import { useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import SyncManager from '../modules/SyncManager';

let syncManagerInstance = null;

const SyncInitializer = () => {
  const { user } = useAuth();

  useEffect(() => {
    if (!syncManagerInstance) {
      syncManagerInstance = new SyncManager({ user });
    }

    if (user) {
      syncManagerInstance.authService.user = user; // Update user in syncManager
      syncManagerInstance.startSync();
    } else {
      syncManagerInstance.stopSync();
    }

    return () => {
      // No need to stop here, as the instance is managed globally or by the last user
      // syncManagerInstance.stopSync(); 
    };
  }, [user]);

  return null; // This component doesn't render anything
};

export default SyncInitializer;
