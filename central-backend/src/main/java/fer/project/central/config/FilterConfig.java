package fer.project.central.config;

import fer.project.central.security.HmacAuthFilter;
import org.springframework.boot.web.servlet.FilterRegistrationBean;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class FilterConfig {

    @Bean
    public FilterRegistrationBean<HmacAuthFilter> hmacAuthFilterRegistration(HmacAuthFilter filter) {
        FilterRegistrationBean<HmacAuthFilter> registration = new FilterRegistrationBean<>();
        registration.setFilter(filter);

        // registriraj na sve API endpoint-e pa unutra filtriraj što štitiš
        registration.addUrlPatterns("/api/v1/*");

        // neka bude rano u lancu
        registration.setOrder(1);

        return registration;
    }
}
