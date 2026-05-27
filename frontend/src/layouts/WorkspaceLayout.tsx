import { Outlet } from '@tanstack/react-router';
import { motion } from 'framer-motion';

export function WorkspaceLayout() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25, ease: 'easeOut' }}
    >
      <Outlet />
    </motion.div>
  );
}
