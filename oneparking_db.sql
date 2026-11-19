-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Servidor: 127.0.0.1
-- Tiempo de generación: 05-05-2026 a las 18:24:35
-- Versión del servidor: 10.4.32-MariaDB
-- Versión de PHP: 8.2.12

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Base de datos: `oneparking_db`
--

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `daily_expenses`
--

CREATE TABLE `daily_expenses` (
  `date` date NOT NULL,
  `total_expenses` int(11) NOT NULL DEFAULT 0
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `daily_expenses`
--

INSERT INTO `daily_expenses` (`date`, `total_expenses`) VALUES
('2026-02-18', 0),
('2026-02-19', 0),
('2026-02-24', 0),
('2026-02-28', 0),
('2026-03-18', 0),
('2026-03-19', 0),
('2026-03-20', 0),
('2026-03-24', 0),
('2026-04-29', 0);

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `daily_income`
--

CREATE TABLE `daily_income` (
  `date` date NOT NULL,
  `total_income` int(11) NOT NULL DEFAULT 0
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `daily_income`
--

INSERT INTO `daily_income` (`date`, `total_income`) VALUES
('2026-02-14', 42000),
('2026-02-18', 321000),
('2026-02-19', 42000),
('2026-02-24', 6000),
('2026-02-28', 606000),
('2026-03-18', 0),
('2026-03-19', 0),
('2026-03-20', 0),
('2026-03-24', 0),
('2026-04-29', 0);

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `daily_net_totals`
--

CREATE TABLE `daily_net_totals` (
  `date` date NOT NULL,
  `net_total` int(11) NOT NULL DEFAULT 0
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `daily_net_totals`
--

INSERT INTO `daily_net_totals` (`date`, `net_total`) VALUES
('2025-11-14', 0),
('2025-11-17', 0),
('2025-11-18', 0),
('2025-11-26', 0),
('2026-02-14', 0),
('2026-02-19', 0),
('2026-02-24', 0),
('2026-02-28', 0),
('2026-03-18', 0),
('2026-03-19', 0),
('2026-03-20', 0),
('2026-03-24', 0),
('2026-04-29', 0);

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `expenses`
--

CREATE TABLE `expenses` (
  `id` int(11) NOT NULL,
  `description` varchar(255) NOT NULL,
  `amount` int(11) NOT NULL,
  `date` date NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `parking_spaces`
--

CREATE TABLE `parking_spaces` (
  `id` int(11) NOT NULL,
  `space_number` varchar(10) NOT NULL,
  `space_type` varchar(20) DEFAULT 'regular',
  `status` varchar(20) DEFAULT 'available',
  `vehicle_plate` varchar(10) DEFAULT NULL,
  `occupied_since` datetime DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `parking_spaces`
--

INSERT INTO `parking_spaces` (`id`, `space_number`, `space_type`, `status`, `vehicle_plate`, `occupied_since`) VALUES
(1, 'A01', 'premium', 'occupied', 'bbb222', '2026-02-19 09:46:00'),
(2, 'A02', 'premium', 'available', NULL, NULL),
(3, 'A03', 'premium', 'available', NULL, NULL),
(4, 'A04', 'premium', 'occupied', 'aaa222', '2026-02-28 20:52:51'),
(5, 'A05', 'premium', 'available', NULL, NULL),
(6, 'A06', 'premium', 'available', NULL, NULL),
(7, 'A07', 'premium', 'available', NULL, NULL),
(8, 'A08', 'premium', 'available', NULL, NULL),
(9, 'A09', 'premium', 'available', NULL, NULL),
(10, 'A10', 'premium', 'available', NULL, NULL),
(11, 'B01', 'regular', 'available', NULL, NULL),
(12, 'B02', 'regular', 'available', NULL, NULL),
(13, 'B03', 'regular', 'available', NULL, NULL),
(14, 'B04', 'regular', 'available', NULL, NULL),
(15, 'B05', 'regular', 'available', NULL, NULL),
(16, 'B06', 'regular', 'available', NULL, NULL),
(17, 'B07', 'regular', 'available', NULL, NULL),
(18, 'B08', 'regular', 'available', NULL, NULL),
(19, 'B09', 'regular', 'available', NULL, NULL),
(20, 'B10', 'regular', 'available', NULL, NULL),
(21, 'C01', 'regular', 'available', NULL, NULL),
(22, 'C02', 'regular', 'available', NULL, NULL),
(23, 'C03', 'regular', 'available', NULL, NULL),
(24, 'C04', 'regular', 'available', NULL, NULL),
(25, 'C05', 'regular', 'available', NULL, NULL),
(26, 'C06', 'regular', 'available', NULL, NULL),
(27, 'C07', 'regular', 'available', NULL, NULL),
(28, 'C08', 'regular', 'available', NULL, NULL),
(29, 'C09', 'regular', 'available', NULL, NULL),
(30, 'C10', 'regular', 'available', NULL, NULL);

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `rates`
--

CREATE TABLE `rates` (
  `vehicle_type` varchar(10) NOT NULL,
  `rate` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `rates`
--

INSERT INTO `rates` (`vehicle_type`, `rate`) VALUES
('carro', 3000),
('cicla', 500),
('moto', 1500);

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `reset_dates`
--

CREATE TABLE `reset_dates` (
  `id` int(11) NOT NULL,
  `last_reset_date` date NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `reset_dates`
--

INSERT INTO `reset_dates` (`id`, `last_reset_date`) VALUES
(41, '2026-02-14'),
(42, '2026-02-14'),
(43, '2026-02-18'),
(44, '2026-02-19'),
(45, '2026-02-24'),
(46, '2026-02-28'),
(47, '2026-03-18'),
(48, '2026-03-19'),
(49, '2026-03-20'),
(50, '2026-03-24'),
(51, '2026-04-29');

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `system_logs`
--

CREATE TABLE `system_logs` (
  `id` int(11) NOT NULL,
  `timestamp` datetime NOT NULL,
  `user` varchar(50) NOT NULL,
  `action` varchar(255) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `system_logs`
--

INSERT INTO `system_logs` (`id`, `timestamp`, `user`, `action`) VALUES
(1, '2025-10-05 08:31:09', 'admin', 'Inicio de sesión exitoso para usuario admin'),
(2, '2025-10-05 08:31:45', 'caja', 'Inicio de sesión exitoso para usuario caja'),
(3, '2025-11-11 19:28:26', 'admin', 'Inicio de sesión exitoso para usuario admin');

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `users`
--

CREATE TABLE `users` (
  `username` varchar(50) NOT NULL,
  `password` varchar(50) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `users`
--

INSERT INTO `users` (`username`, `password`) VALUES
('admin', '1234'),
('caja', 'caja123');

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `vehicles`
--

CREATE TABLE `vehicles` (
  `id` int(11) NOT NULL,
  `plate` varchar(10) NOT NULL,
  `vehicle_type` varchar(10) NOT NULL,
  `entry_time` datetime NOT NULL,
  `exit_time` datetime DEFAULT NULL,
  `cost` int(11) DEFAULT NULL,
  `space_id` int(11) DEFAULT NULL,
  `exit_timer_end` datetime DEFAULT NULL COMMENT 'Fecha/hora límite para salida después del pago'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `vehicles`
--

INSERT INTO `vehicles` (`id`, `plate`, `vehicle_type`, `entry_time`, `exit_time`, `cost`, `space_id`, `exit_timer_end`) VALUES
(8015, 'hiu091', 'carro', '2026-02-14 07:55:54', '2026-02-14 07:56:10', 3000, 1, NULL),
(8016, 'AAA111', 'carro', '2026-02-14 07:56:46', '2026-02-14 07:56:58', 3000, 1, NULL),
(8017, 'hiu091', 'carro', '2026-02-14 07:59:16', '2026-02-14 07:59:34', 3000, 1, NULL),
(8018, 'hiu091', 'carro', '2026-02-14 08:39:48', '2026-02-14 08:41:45', 3000, 1, NULL),
(8019, 'hiu091', 'carro', '2026-02-14 08:43:42', '2026-02-18 18:26:20', 318000, 1, NULL),
(8020, 'hiu091', 'carro', '2026-02-18 19:53:04', '2026-02-19 09:45:45', 42000, 1, '2026-02-19 09:45:45'),
(8021, 'bbb222', 'carro', '2026-02-19 09:46:00', NULL, NULL, 1, NULL),
(8022, 'zod562', 'carro', '2026-02-24 15:57:57', '2026-02-28 20:55:23', 303000, 2, '2026-02-28 20:55:23'),
(8023, 'hvv497', 'carro', '2026-02-24 16:00:28', '2026-02-28 20:59:01', 303000, 3, '2026-02-28 20:59:01'),
(8024, 'aaa222', 'carro', '2026-02-28 20:52:51', NULL, NULL, 4, NULL);

--
-- Índices para tablas volcadas
--

--
-- Indices de la tabla `daily_expenses`
--
ALTER TABLE `daily_expenses`
  ADD PRIMARY KEY (`date`);

--
-- Indices de la tabla `daily_income`
--
ALTER TABLE `daily_income`
  ADD PRIMARY KEY (`date`);

--
-- Indices de la tabla `daily_net_totals`
--
ALTER TABLE `daily_net_totals`
  ADD PRIMARY KEY (`date`);

--
-- Indices de la tabla `expenses`
--
ALTER TABLE `expenses`
  ADD PRIMARY KEY (`id`);

--
-- Indices de la tabla `parking_spaces`
--
ALTER TABLE `parking_spaces`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `space_number` (`space_number`);

--
-- Indices de la tabla `rates`
--
ALTER TABLE `rates`
  ADD PRIMARY KEY (`vehicle_type`);

--
-- Indices de la tabla `reset_dates`
--
ALTER TABLE `reset_dates`
  ADD PRIMARY KEY (`id`);

--
-- Indices de la tabla `system_logs`
--
ALTER TABLE `system_logs`
  ADD PRIMARY KEY (`id`);

--
-- Indices de la tabla `users`
--
ALTER TABLE `users`
  ADD PRIMARY KEY (`username`);

--
-- Indices de la tabla `vehicles`
--
ALTER TABLE `vehicles`
  ADD PRIMARY KEY (`id`);

--
-- AUTO_INCREMENT de las tablas volcadas
--

--
-- AUTO_INCREMENT de la tabla `expenses`
--
ALTER TABLE `expenses`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=353;

--
-- AUTO_INCREMENT de la tabla `parking_spaces`
--
ALTER TABLE `parking_spaces`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=32;

--
-- AUTO_INCREMENT de la tabla `reset_dates`
--
ALTER TABLE `reset_dates`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=52;

--
-- AUTO_INCREMENT de la tabla `system_logs`
--
ALTER TABLE `system_logs`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=4;

--
-- AUTO_INCREMENT de la tabla `vehicles`
--
ALTER TABLE `vehicles`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=8025;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
