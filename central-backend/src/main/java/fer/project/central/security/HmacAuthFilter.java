package fer.project.central.security;

import fer.project.central.controller.util.HmacValidator;
import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.time.LocalDateTime;
import java.time.ZoneOffset;
import java.time.format.DateTimeParseException;

@Component
@RequiredArgsConstructor
@Slf4j
public class HmacAuthFilter extends OncePerRequestFilter {

    private static final String SIGNATURE_HEADER = "X-HMAC-Signature";
    private static final String TIMESTAMP_HEADER = "X-Timestamp";

    /**
     * Replay protection window.
     * - If you send timestamps in seconds: allow e.g. 60s drift
     * - If you send timestamps in millis: still works
     */
    private static final long ALLOWED_DRIFT_SECONDS = 60;

    private final HmacValidator hmacValidator;

    @Override
    protected boolean shouldNotFilter(HttpServletRequest request) {
        String uri = request.getRequestURI();
        String method = request.getMethod();

        boolean userIngest  = uri.equals("/api/v1/user") && method.equalsIgnoreCase("POST");
        boolean btsRegister = uri.equals("/api/v1/bts")  && method.equalsIgnoreCase("POST");
        boolean btsStatus   = uri.matches("^/api/v1/bts/[^/]+/status$") && method.equalsIgnoreCase("PATCH");

        // zaštiti samo ova 3 write endpointa
        return !(userIngest || btsRegister || btsStatus);
    }

    @Override
    protected void doFilterInternal(HttpServletRequest request,
                                    HttpServletResponse response,
                                    FilterChain filterChain) throws ServletException, IOException {

        log.info("HMAC FILTER HIT {} {}", request.getMethod(), request.getRequestURI());

        String tsHeader = request.getHeader(TIMESTAMP_HEADER);
        String sigHeader = request.getHeader(SIGNATURE_HEADER);

        if (isBlank(tsHeader) || isBlank(sigHeader)) {
            log.warn("HMAC FILTER REJECTED (missing headers) {} {}", request.getMethod(), request.getRequestURI());
            writeError(response, HttpStatus.UNAUTHORIZED, request.getRequestURI());
            return;
        }

        Long tsSeconds = parseToEpochSeconds(tsHeader);
        if (tsSeconds == null) {
            log.warn("HMAC FILTER REJECTED (bad timestamp format) {} {}", request.getMethod(), request.getRequestURI());
            writeError(response, HttpStatus.UNAUTHORIZED, request.getRequestURI());
            return;
        }

        long nowSeconds = System.currentTimeMillis() / 1000;
        if (Math.abs(nowSeconds - tsSeconds) > ALLOWED_DRIFT_SECONDS) {
            log.warn("HMAC FILTER REJECTED (timestamp out of window) {} {} (now={}, ts={}, drift={}s)",
                    request.getMethod(),
                    request.getRequestURI(),
                    nowSeconds,
                    tsSeconds,
                    Math.abs(nowSeconds - tsSeconds)
            );
            writeError(response, HttpStatus.UNAUTHORIZED, request.getRequestURI());
            return;
        }

        // pročitaj body jednom i wrapaj request da ga controller može opet čitati
        byte[] bodyBytes = request.getInputStream().readAllBytes();
        String body = new String(bodyBytes, StandardCharsets.UTF_8);

        boolean ok = hmacValidator.validate(body, tsHeader.trim(), sigHeader.trim());
        if (!ok) {
            log.warn("HMAC FILTER REJECTED (invalid signature) {} {}", request.getMethod(), request.getRequestURI());
            writeError(response, HttpStatus.UNAUTHORIZED, request.getRequestURI());
            return;
        }

        CachedBodyHttpServletRequest wrapped = new CachedBodyHttpServletRequest(request, bodyBytes);
        filterChain.doFilter(wrapped, response);
    }

    /**
     * Accepts timestamps in:
     - iso8601 format (no timestamp, local time)
     */
    private Long parseToEpochSeconds(String tsHeader) {
        try {
            String s = tsHeader.trim();
            log.error("Received value: '{}'", s); 
            return LocalDateTime.parse(s).toEpochSecond(ZoneOffset.UTC);
        } catch (DateTimeParseException e) {
            return null;
        }
    }

    private boolean isBlank(String s) {
        return s == null || s.trim().isEmpty();
    }

    private void writeError(HttpServletResponse response, HttpStatus status, String path) throws IOException {
        response.resetBuffer();
        response.setStatus(status.value());
        response.setContentType("application/json");
        response.setCharacterEncoding(StandardCharsets.UTF_8.name());

        String body = """
            {
              "timestamp":"%s",
              "status":%d,
              "error":"%s",
              "path":"%s"
            }
            """.formatted(
                LocalDateTime.now(),
                status.value(),
                status.getReasonPhrase(),
                path
            );

        response.getWriter().write(body);
        response.flushBuffer();
    }
}
