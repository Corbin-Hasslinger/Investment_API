import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { RouterTestingHarness } from '@angular/router/testing';
import { routes } from './app.routes';
import { App } from './app';

describe('App', () => {
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [App],
      providers: [provideRouter(routes)],
    }).compileComponents();
  });

  it('should create the app', () => {
    const fixture = TestBed.createComponent(App);
    expect(fixture.componentInstance).toBeTruthy();
  });

  it('renders the app shell with sidebar navigation links', async () => {
    const fixture = TestBed.createComponent(App);
    await fixture.whenStable();
    const compiled = fixture.nativeElement as HTMLElement;
    const links = Array.from(compiled.querySelectorAll('nav a')).map((a) => a.textContent?.trim());

    expect(links).toEqual(['Dashboard', 'Portfolios', 'Research', 'Stock Screener']);
  });

  it('navigates to the portfolios page', async () => {
    const harness = await RouterTestingHarness.create();
    const instance = await harness.navigateByUrl('/portfolios');
    expect(instance).toBeTruthy();
    expect(harness.routeNativeElement?.textContent).toContain('portfolio-list-page works!');
  });

  it('redirects an unknown route to the dashboard', async () => {
    const harness = await RouterTestingHarness.create();
    await harness.navigateByUrl('/does-not-exist');
    expect(harness.routeNativeElement?.textContent).toContain('dashboard-page works!');
  });
});
