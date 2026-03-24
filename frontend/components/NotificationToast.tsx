
import React, { useState, useEffect } from 'react';
import { CheckCircleIcon, ExclamationCircleIcon, InformationCircleIcon } from './Icons';
import { Notification } from '../types';

interface NotificationToastProps {
  notification: Notification;
  onClose: () => void;
}

const NotificationToast: React.FC<NotificationToastProps> = ({ notification, onClose }) => {
  const [show, setShow] = useState(false);

  useEffect(() => {
    // Component did mount, trigger fade in
    const showTimer = setTimeout(() => setShow(true), 10);
    // Before component unmounts, trigger fade out
    const hideTimer = setTimeout(() => setShow(false), 4500); 

    return () => {
      clearTimeout(showTimer);
      clearTimeout(hideTimer);
    };
  }, []);

  const { message, type } = notification;

  const icons = {
    success: <CheckCircleIcon />,
    warning: <ExclamationCircleIcon />,
    info: <InformationCircleIcon />,
  };

  const themeClasses = {
    success: 'bg-green-100 dark:bg-green-800/50 text-green-800 dark:text-green-200 border-green-300 dark:border-green-600',
    warning: 'bg-yellow-100 dark:bg-yellow-800/50 text-yellow-800 dark:text-yellow-200 border-yellow-300 dark:border-yellow-600',
    info: 'bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-200 border-gray-300 dark:border-gray-600',
  };

  return (
    <div
      className={`max-w-sm w-full rounded-lg shadow-lg pointer-events-auto ring-1 ring-black ring-opacity-5 overflow-hidden border ${themeClasses[type]} transition-all duration-300 ease-in-out transform ${show ? 'translate-x-0 opacity-100' : 'translate-x-full opacity-0'}`}
      role="alert"
    >
      <div className="p-4">
        <div className="flex items-start">
          <div className="flex-shrink-0">{icons[type]}</div>
          <div className="ml-3 w-0 flex-1 pt-0.5">
            <p className="text-sm font-medium">{message}</p>
          </div>
          <div className="ml-4 flex-shrink-0 flex">
            <button onClick={onClose} className="rounded-md inline-flex text-gray-400 dark:text-gray-300 hover:text-gray-600 dark:hover:text-white focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 dark:focus:ring-offset-gray-800">
              <span className="sr-only">Close</span>
              <svg className="h-5 w-5" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
                <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
              </svg>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default NotificationToast;
